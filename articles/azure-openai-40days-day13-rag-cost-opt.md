---
title: "【Azure OpenAI 40日】 Day13：RAGを速く・安く — キャッシュ×topK最適化"
emoji: "🚀"
type: "tech"
topics: ["azure","openai","python","promptflow","rag"]
published: false
---

## ✍️ TL;DR
- 2回目実行で **`search/llm: cache`** を確認（ログ＋スクショで証跡化）。
- **topK↑ ⇒ 遅延↑／トークン↑** を `results.csv` とグラフで可視化。
- **文脈圧縮（MAX_CHARS）** で prompt tokens を削減。暫定ベースラインは **`topK=3 / MAX_CHARS=800 / USE_SEMANTIC=0`**。
- 次回 Day14 は `results.csv` を使い **自動評価（スコアリング）** を実装。

---

## 🧭 今日のゴール
- キャッシュ挙動の**証跡（スクショ＆CSV）**を残す
- **topK／圧縮／セマンティック**の効果を**グラフで可視化**
- **ベースライン設定**を決めて `.env` に固定、記事化まで完了

---

## 🔧 手順（そのまま実行可）

### PowerShell/CLI
```powershell
# 1) .env の暫定ベースライン
notepad C:\dev\azure-ai-40days\.env
# 推奨:
# USE_SEMANTIC=0
# MAX_CHARS=800
# TOPK_LIST=1,3,5
# INPUT_PRICE_PER1K=0.0
# OUTPUT_PRICE_PER1K=0.0

# 2) キャッシュ挙動の確認（同一クエリを2回）
cd C:\dev\azure-ai-40days\day13
python .\day13_rag_opt.py "RAGのキャッシュ最適化の方法を要約して"
python .\day13_rag_opt.py "RAGのキャッシュ最適化の方法を要約して"

# 3) 条件マトリクスでベンチ（429緩和に短いスリープ）
$queries = @(
  "RAGのキャッシュ最適化の方法を要約して",
  "topKはなぜコストに影響するのかを説明して",
  "Azure AI Searchのインデクサー失敗時の対処を教えて",
  "gpt-4o-miniで入力トークンを削減するコツは？",
  "RAG評価で見るべきメトリクスは？"
)
$ErrorActionPreference = "Stop"
Remove-Item .\results.csv -ErrorAction SilentlyContinue
$env:USE_SEMANTIC="0"     # Semantic未構成ならOFF
$maxchars = @("0","800") # 無圧縮 vs 軽圧縮
$env:TOPK_LIST="1,3,5"
foreach($m in $maxchars){
  $env:MAX_CHARS=$m
  foreach($q in $queries){
    python .\day13_rag_opt.py "$q"
    Start-Sleep -Milliseconds 200
  }
}

# 4) 可視化（PNGを出力）
python .\viz_results.py
```

### Python（最小実装例：環境変数で実行条件を切替）
```python
# 実行イメージ（本体は day13/day13_rag_opt.py に実装済み）
import os, subprocess
os.environ["USE_SEMANTIC"] = "0"
os.environ["MAX_CHARS"] = "800"
os.environ["TOPK_LIST"] = "3"
subprocess.run(["python", "day13_rag_opt.py", "RAGのキャッシュ最適化の方法を要約して"])
```
> ⚠️注意：キー等の秘密情報は `.env` に保存し、記事やリポジトリに直書きしない。

---

## ✅ 検証結果
- **キャッシュ**：同一クエリ2回目で `search: cache / llm: cache` を確認（スクショ取得）。
- **可視化**：以下の3枚が `images/day13/` に生成される。
  - `llm_latency_by_topk.png` — topK別の平均LLM遅延
  - `tokens_compress.png` — 圧縮ON/OFFと入力トークン
  - `cost_semantic.png` — semantic ON/OFFと推定コスト

![](/images/day13/llm_latency_by_topk.png)
![](/images/day13/tokens_compress.png)
![](/images/day13/cost_semantic.png)

---

## 🧯 つまずき＆対処
| エラー/症状 | 原因 | 対処（優先度順） |
|---|---|---|
| `Semantic search is not enabled ...` | SearchにSemantic構成なし | `.env: USE_SEMANTIC=0`。コードは**自動フォールバック**済み |
| `429 Too Many Requests` | レート超過 | 200msスリープ、topK縮小、圧縮ON（トークン削減）。**指数バックオフ＋ジッタ**で再送 |
| `401/403/404` | キー/デプロイ名/インデックス名不一致 | `.env` を再確認（URLは `https://` を含む）。Portalで名称確認 |
| `results.csv` がロック | Excelで開きっぱなし | Excelを閉じて再実行 |
| 回答が一般論に寄る | 本文フィールド不一致/ヒット弱 | `_extract_doc_text()` の候補に実フィールド追加、データ見直し |

---

## 💰 コストメモ
- 概算式：`(prompt_tokens/1000)*入力単価 + (completion_tokens/1000)*出力単価`
- 削減の優先順：**topK最小化 → 圧縮（MAX_CHARS） → system短縮 → mini系モデル → キャッシュ**
- 単価は `.env` の `INPUT_PRICE_PER1K` / `OUTPUT_PRICE_PER1K` で管理

---

## 📌 Day13でやったこと振り返り
1. キャッシュ×topKの最小実装を動かし、**ログ/画像で可視化**
2. **429/semantic未対応**に強いリトライ＆フォールバックを実装
3. 暫定ベースラインを決定（`topK=3, MAX_CHARS=800, USE_SEMANTIC=0`）

---

## 🔮 次回の予告（Day14）
- `results.csv` / （任意）`answers.jsonl` を入力に **自動評価（キーワード採点/LLM判定）** を実装
- `topK / 圧縮 / semantic` の**ベスト設定**をスコアで決定

---

## 📚 参考リンク
- Azure OpenAI / Azure AI Search 公式ドキュメント
- 評価・可視化の一般的手法（confusion matrix, latency/throughput測定 など）

