---
title: "【Azure OpenAI 40日】Day12：Blob追加→Search増分インデクシングを一気通貫"
emoji: "⚙️"
type: "tech"
topics: ["azure","cognitive-search","blob-storage","rag","python"]
published: true
---

## TL;DR
- Blob に追補 → Indexer を**手動実行**して増分取り込み。
- `status: success / failed=0`、`document_count` 増を確認。
- ユニーク語（Day12Marker）で**新規ファイルのヒット**を確定。
- コストは Search/Blob の I/O＋呼び出し数。**429対策（バックオフ）**は実装推奨。

## 今日のゴール
- 新規ドキュメントを追加し、**増分インデクシング→検索で反映確認**。

## 目的と背景
- **目的**: Blob や Azure Cognitive Search のデータを安全に更新し、即時に結果へ反映できる運用ルーチンを確立する。  
- **背景**: Day10–11 で最小RAGを構築済み。Day12は「新規データアップロード → 増分インデクシング → 更新後の動作確認」を通して、RAG運用の基礎体力をつける（データ更新と再インデクシング）。

## 実行環境
- Windows 11 / PowerShell 5.1 以上（PS7推奨）
- Python 3.x（venv）
- ライブラリ: `azure-storage-blob`, `azure-search-documents`, `requests`
- **環境変数（値は伏せる）**:  
  `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_ADMIN_KEY`,  
  `INDEX_NAME`, `INDEXER_NAME`, `BLOB_CONTAINER`

## 手順（最小）
```powershell
# プロジェクト直下
cd C:\dev\azure-ai-40days\
.venv\Scripts\Activate.ps1

# 依存ライブラリ
pip install "azure-storage-blob>=12.20.0" "azure-search-documents==11.5.3" requests

# 追補ファイルを作成（例）
@'
# よくあるエラーと対処（追補）
- エラー: 接続タイムアウト → ネットワーク/プロキシ確認と再試行
- エラー: 401 Unauthorized → キー・エンドポイント・デプロイ名を再確認
'@ | Out-File -Encoding UTF8 .\day12\errors_jp.md

@'
# FAQ（追補）
Q: インデクサー実行の所要時間は？
A: 差分量に依存。失敗時はステータスを確認して再実行。
'@ | Out-File -Encoding UTF8 .\day12\faq_jp.md

# 既定値（未設定ならセット）— PowerShell 5.1 互換
if (-not $env:BLOB_CONTAINER) { $env:BLOB_CONTAINER = "docs" }
if (-not $env:INDEX_NAME)     { $env:INDEX_NAME     = "docs-idx" }
if (-not $env:INDEXER_NAME)   { $env:INDEXER_NAME   = "blob-idxr" }

# インデクサー実行（アップロード→run→検証）
python .\day12\reindex.py
````

## コード（抜粋）

`day12/reindex.py`（429/409対策のバックオフ入り）

```python
import os, time, requests
from azure.storage.blob import BlobClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

CONN = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
ENDP = os.environ["AZURE_SEARCH_ENDPOINT"].strip().rstrip("/")
ADMIN= os.environ["AZURE_SEARCH_ADMIN_KEY"]
INDEX= os.environ.get("INDEX_NAME","docs-idx")
INDEXER=os.environ.get("INDEXER_NAME","blob-idxr")
CONT = os.environ.get("BLOB_CONTAINER","docs")

def upload(local_path, blob_name):
    bc = BlobClient.from_connection_string(CONN, container_name=CONT, blob_name=blob_name)
    with open(local_path, "rb") as f:
        bc.upload_blob(f, overwrite=True)
    print(f"[upload] {blob_name}")

def run_indexer_with_backoff(max_attempts=5):
    url_run    = f"{ENDP}/indexers/{INDEXER}/run?api-version=2024-07-01"
    url_status = f"{ENDP}/indexers/{INDEXER}/status?api-version=2024-07-01"
    headers    = {"api-key": ADMIN}
    # 既に実行中なら完了まで待つ
    try:
        st = requests.get(url_status, headers=headers).json().get("lastResult", {})
        if st.get("status") == "inProgress":
            print("[indexer] already running; waiting for completion...")
            wait_status()
    except Exception as e:
        print("[warn] status check failed:", e)

    delay = 5
    for attempt in range(1, max_attempts + 1):
        r = requests.post(url_run, headers=headers)
        if r.status_code == 202:
            print("[indexer] run accepted")
            return
        if r.status_code in (429, 409):
            print(f"[indexer] {r.status_code} retrying in {delay}s (attempt {attempt}/{max_attempts})")
            time.sleep(delay)
            delay = min(delay * 2, 60)
            continue
        r.raise_for_status()
    raise RuntimeError("failed to start indexer after retries")

def wait_status(timeout=180):
    url = f"{ENDP}/indexers/{INDEXER}/status?api-version=2024-07-01"
    t0=time.time()
    while True:
        st = requests.get(url, headers={"api-key": ADMIN}).json()["lastResult"]
        print(f"[status] {st['status']} processed={st.get('itemsProcessed')} failed={st.get('itemsFailed')}")
        if st["status"] in ("success","transientFailure","error"):
            return st
        if time.time()-t0>timeout:
            raise TimeoutError("indexer timeout")
        time.sleep(5)

def verify():
    sc = SearchClient(endpoint=ENDP, index_name=INDEX, credential=AzureKeyCredential(ADMIN))
    cnt = sc.get_document_count()
    print("[verify] document_count =", cnt)
    hits = list(sc.search("エラー 対処", top=3, query_type="simple", search_fields=["content"]))
    print("[verify] query 'エラー 対処' hits:", [h.get("metadata_storage_name") for h in hits])

if __name__ == "__main__":
    base = r"C:\dev\azure-ai-40days\day12"
    upload(os.path.join(base,"errors_jp.md"), "errors_jp.md")
    upload(os.path.join(base,"faq_jp.md"), "faq_jp.md")
    run_indexer_with_backoff()
    last = wait_status()
    assert last["itemsFailed"] == 0, "indexer failed items > 0"
    verify()
    print("[done] Day12 reindex completed")
```

`day12/quick_search.py`（新語句ヒットの確定）

```python
import os, sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

def need(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"環境変数 {name} が未設定です。")
    return v

print("quick_search.py start")  # 起動確認

ENDP  = need("AZURE_SEARCH_ENDPOINT").rstrip("/")
ADMIN = need("AZURE_SEARCH_ADMIN_KEY")
INDEX = os.environ.get("INDEX_NAME", "docs-idx")
query = " ".join(sys.argv[1:]) or "Day12Marker"
print(f"query: {query}")

client = SearchClient(endpoint=ENDP, index_name=INDEX, credential=AzureKeyCredential(ADMIN))
results = client.search(
    query,
    top=5,
    query_type="simple",
    search_fields=["content"],
    highlight_fields="content",
    highlight_pre_tag="[",
    highlight_post_tag="]"
)

found = False
for r in results:
    found = True
    name = r.get("metadata_storage_name")
    score = r.get("@search.score")
    score_str = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
    snippet = ""
    hl = r.get("@search.highlights")
    if isinstance(hl, dict) and hl.get("content"):
        snippet = hl["content"][0]
    print(f"- {name}  score={score_str}")
    if snippet:
        print(f"  snippet: {snippet}")

if not found:
    print("(no hits)")
```

## 実行結果（スクリーンショット）

1. **Indexer 成功ログ**
   `images/day12/indexer-success.png`
   ![Indexer success](/images/day12/indexer-success.png)

2. **document\_count 増加**
   `images/day12/document-count-increase.png`
   ![Document count increase](/images/day12/document-count-increase.png)

3. **新規語句ヒット（Day12Marker）**
   `images/day12/quick-search-hit.png`
   ![New term hit (Day12Marker)](/images/day12/quick-search-hit.png)

## 検証チェック

* `status: success / failed=0` が出ている
* `document_count` が **前回より増**えている
* `Day12Marker`（または新規語句）で **`errors_jp.md` がヒット**

## つまずき＆対処

* **429 Too Many Requests** → レート制限。**30–60秒待機** or 上記バックオフ関数で自動再試行。
* **401 Unauthorized** → 管理キー/エンドポイント不一致。`AZURE_SEARCH_ENDPOINT` は末尾 `/` なし。
* **unsupported file type** → `.md/.txt` の **UTF-8（BOMなし）** に統一。
* **ヒットしない** → 反映待ち（数十秒）→ `filter="metadata_storage_name eq 'errors_jp.md'"` で存在確認。

## コストメモ

* 概算: 「Indexer 実行×回数」＋「検索クエリ数」＋ Blob の PUT/容量
* 削減: 変更を**まとめて1回 `/run`**、ログを短く、**バックオフ**で無駄叩きを避ける

## 次回予告（Day13）

`search_fields` の最適化やスコアリング、回答への**引用必須**設定で検索品質を底上げします。
