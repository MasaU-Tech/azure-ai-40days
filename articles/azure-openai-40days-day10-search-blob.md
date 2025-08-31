---
title: "【Azure OpenAI 40日】 Day10：Blob→Azure AI Searchで最小RAGを構築"
emoji: "🔎"
type: "tech"
topics: ["azure","search","blob","python","rag"]
published: true
---

## ✍️ TL;DR
- 今日の到達点：Blobに置いたMarkdown/テキストを **Indexer** でSearchへ自動取り込みし、Pythonから検索ヒットを確認
- 学び：
  - RG再利用で資産を持ち越す運用が楽になる
  - Index → Data Source → Indexer の順で作ると事故りにくい
  - つまずきは「キー不一致」「不要設定」で起きやすいが最小構成で回避できる
- コスト：Search Freeで0円（不可ならBasicの時間課金/短時間）＋ Storageはほぼゼロ

---

## 🧭 今日のゴール
- 既存RG（Japan East）上で **Blob → Search** の最小RAG土台を作る
- **Index / Data Source / Indexer** を作成・実行
- `document_count=2` と検索ヒットを確認

---

## 🎯 目的と背景
- **目的**: 自分のデータをAIに検索させ、応答の精度を高める。  
- **背景**: RAGは実務AI導入の王道。社内文書活用など実践的シナリオに直結する。

---

## 🔧 手順（そのまま実行可）

### PowerShell/CLI
```powershell
# 既存RGを利用（例: rg-aoai40-main）
$RG="<既存RG名>"; $LOC="japaneast"
az configure --defaults group=$RG location=$LOC

# 一意名
$RAND=(Get-Random -Maximum 9999).ToString("0000")
$SA="ai40d10$RAND"; $CONT="docs"; $SEARCH="ai40d10search$RAND"

# Storage & 接続文字列（RBAC待ちを回避）
az storage account create -n $SA --sku Standard_LRS --kind StorageV2
$env:AZURE_STORAGE_CONNECTION_STRING = az storage account show-connection-string -n $SA -o tsv
az storage container create --name $CONT --connection-string $env:AZURE_STORAGE_CONNECTION_STRING

# サンプル文書
$DOCROOT="C:\dev\azure-ai-40days\day10\sample"; New-Item -ItemType Directory -Force $DOCROOT | Out-Null
@'
# 社内手順メモ
Azure OpenAI と Azure AI Search を連携して RAG を構成する。
手順:
1. Storage に資料を置く
2. Indexer を実行
'@ | Set-Content -Encoding UTF8 "$DOCROOT\readme.md"
"Azure AI Search はフルテキスト検索を提供します。" | Set-Content -Encoding UTF8 "$DOCROOT\note.txt"

az storage blob upload-batch --destination $CONT --source $DOCROOT `
  --connection-string $env:AZURE_STORAGE_CONNECTION_STRING

# Search（Free→失敗時Basic）
az search service create --name $SEARCH --sku free --partition-count 1 --replica-count 1
if ($LASTEXITCODE -ne 0) { az search service create --name $SEARCH --sku basic --partition-count 1 --replica-count 1 }

# エンドポイント/キー
$env:AZURE_SEARCH_ENDPOINT=("https://{0}.search.windows.net" -f $SEARCH)
$env:AZURE_SEARCH_ADMIN_KEY=(az search admin-key show --service-name $SEARCH --query primaryKey -o tsv).Trim()

# 検証用
$env:INDEX_NAME="docs-idx"; $env:BLOB_CONTAINER=$CONT
````

### Python（最小実装）

```python
# FILE: day10/setup_rag_blob_search.py
import os, time
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType,
    SearchIndexerDataSourceConnection, SearchIndexerDataContainer,
    SearchIndexer
)
from azure.search.documents import SearchClient

endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].strip().rstrip("/")
key=os.environ["AZURE_SEARCH_ADMIN_KEY"].strip()
index_name=os.getenv("INDEX_NAME","docs-idx")
container=os.getenv("BLOB_CONTAINER","docs")
conn_str=os.environ["AZURE_STORAGE_CONNECTION_STRING"].strip()

# Index
idxc=SearchIndexClient(endpoint, AzureKeyCredential(key))
fields=[
  SimpleField(name="id", type=SearchFieldDataType.String, key=True),
  SearchableField(name="content", type=SearchFieldDataType.String),
  SimpleField(name="metadata_storage_name", type=SearchFieldDataType.String, filterable=True),
  SimpleField(name="metadata_storage_path", type=SearchFieldDataType.String, filterable=True),
]
idx=SearchIndex(name=index_name, fields=fields)
idxc.create_or_update_index(idx)

# Data Source & Indexer（最小：parameters無し）
ixc=SearchIndexerClient(endpoint, AzureKeyCredential(key))
ds=SearchIndexerDataSourceConnection(
  name="blob-ds", type="azureblob", connection_string=conn_str,
  container=SearchIndexerDataContainer(name=container)
)
ixc.create_or_update_data_source_connection(ds)
ix=SearchIndexer(name="blob-idxr", data_source_name="blob-ds", target_index_name=index_name)
ixc.create_or_update_indexer(ix)
ixc.run_indexer("blob-idxr")

# シンプルに待ってから検索
time.sleep(10)
sc=SearchClient(endpoint, index_name, AzureKeyCredential(key))
for d in sc.search("Azure", top=3):
    print(d.get("metadata_storage_name"), (d.get("content","")[:60] or "").replace("\n"," "))
```

---

## ✅ 検証結果

* 端末出力例（OKサイン）

```text
document_count = 2
- note.txt Azure AI Search はフルテキスト検索を提供します。
- readme.md # 社内手順メモ Azure OpenAI と Azure AI Search を連携して...
```

  ![Search Overview](/images/day10/search-overview.png)

  ![Index Fields](/images/day10/search-index-fields.png)
  
  ![Indexer Success](/images/day10/search-indexer-success.png)
  
  ![Blob List](/images/day10/blob-container-list.png)
  
  ![Terminal](/images/day10/terminal-search-result.png)

---

## 🧯 つまずき＆対処

| エラー/症状（実際に発生）                                                                                     | 主因                                                                            | 対処（優先度順で実行）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `The given API key doesn't match service's internal, primary or secondary keys.`                  | **エンドポイント名とキーのサービス名ズレ**／`-o tsv` の**改行混入**／**Query key誤用**                    | 1) 正しいサービス名で再設定<br>`powershell\n$SEARCH='<実際のSearch名>'\n$env:AZURE_SEARCH_ENDPOINT=(\"https://{0}.search.windows.net\" -f $SEARCH)\n$env:AZURE_SEARCH_ADMIN_KEY=(az search admin-key show --service-name $SEARCH --query primaryKey -o tsv).Trim()\n`2) 健全性チェック（200が返ればOK）<br>\`\`\`powershell\n\$h=@{'api-key'=\$env\:AZURE\_SEARCH\_ADMIN\_KEY}\nInvoke-WebRequest -UseBasicParsing -Method GET -Uri "\$env\:AZURE\_SEARCH\_ENDPOINT/indexes?api-version=2024-07-01" -Headers \$h           | % StatusCode\n`3) 直らない場合は **admin key 再発行**→再設定<br>`powershell\naz search admin-key renew --service-name \$SEARCH --key-kind primary\n\$env\:AZURE\_SEARCH\_ADMIN\_KEY=(az search admin-key show --service-name \$SEARCH --query primaryKey -o tsv).Trim()\n\`\`\`                                                                                                                             |
| `Configuration property 'queryTimeout' is not supported for the data source of type 'azureblob'.` | \*\*Blobでは非対応の設定（queryTimeout）\*\*が `IndexingParametersConfiguration` 経由で送られた | 1) **IndexingParameters/Configuration を外す**最小構成でIndexerを作成<br>（既存スクリプトは修正済み：`SearchIndexer(... parameters なし)`）<br>2) 既に壊れたIndexERがある場合は**削除→再作成**<br>`python\ntry: ixr_client.delete_indexer('blob-idxr')\nexcept Exception: pass\n# → 最小構成で create_or_update_indexer\n`3) それでも不安定なら **RESTで最小JSON** をPUT（`parameters` なし）                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                                                                                |
| `document_count = 2` だが `itemsProcessed = 0`（status は `success`）                                  | **最新実行**では差分が無かった（初回で既に取り込み済み）。`itemsProcessed` は**その実行回**の処理数                | 1) 実行履歴を確認して理解を合わせる：<br>\`\`\`powershell\n\$h=@{'api-key'=\$env\:AZURE\_SEARCH\_ADMIN\_KEY}\n\$st=Invoke-RestMethod -Method GET -Uri "\$env\:AZURE\_SEARCH\_ENDPOINT/indexers/blob-idxr/status?api-version=2024-07-01" -Headers \$h\n\$st.executionHistory                                                                                                                                                                                                                                    | Select-Object -First 3 startTime,status,itemsProcessed,itemsFailed\n`2) テストで再処理させたい場合：**reset→run**<br>`powershell\nInvoke-RestMethod -Method POST -Uri "\$env\:AZURE\_SEARCH\_ENDPOINT/indexers/blob-idxr/reset?api-version=2024-07-01" -Headers \$h\nInvoke-RestMethod -Method POST -Uri "\$env\:AZURE\_SEARCH\_ENDPOINT/indexers/blob-idxr/run?api-version=2024-07-01" -Headers \$h\n\`\`\` |
| 端末出力で `ote.txt` や `te.txt` など**先頭が欠けて見える**                                                        | 表示整形の都合（repr/先頭スペース）による**見た目だけの崩れ**                                           | 1) **名前だけ**列挙して確認：<br>`powershell\npython - << 'PY'\nimport os\nfrom azure.core.credentials import AzureKeyCredential\nfrom azure.search.documents import SearchClient\nsc=SearchClient(os.environ['AZURE_SEARCH_ENDPOINT'].strip(), os.environ.get('INDEX_NAME','docs-idx'), AzureKeyCredential(os.environ['AZURE_SEARCH_ADMIN_KEY'].strip()))\nprint('names:')\nfor d in sc.search('*', top=10):\n    print('-', d.get('metadata_storage_name'))\nPY\n`（`note.txt` と `readme.md` が表示されればOK） |                                                                                                                                                                                                                                                                                                                                                                                                |
| `pip install "azure-search-documents>=11.6.0"` が失敗                                                | 11.6 は **pre-release のみ**で、pip既定では拾わない                                        | 1) **安定版に固定**：`pip install "azure-search-documents==11.5.3"`（本日のコードはこれでOK）<br>2) どうしても 11.6 系なら `--pre` でベータを明示：`pip install --pre "azure-search-documents==11.6.0b12"`                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                |

---

## 💰 コストメモ

* **今日**: Search Free（0円）/ Basic（短時間）、Storageは数ファイルで微小
* **削減**: 使い終わったら Search サービスを削除、クエリ件数/頻度の抑制
* **持ち越し**: Day11〜14で同じ Search/Blob を拡張（RGは再利用）

---

## 📌 Day10でやったこと振り返り

1. Storageに文書を置き、SearchでIndex/DataSource/Indexerを作成
2. Indexerを実行して取り込み成功を確認
3. Pythonから検索し、アップした文書にヒットすることを確認

---

## 🔮 次回の予告

* Day11：**RAGクエリ最適化**（同義語やテンプレ設計、比較検証）