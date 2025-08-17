---
title: "【Azure OpenAI 40日】Day6: プロンプト改善を定量評価する"
emoji: "📊"
type: "tech"
topics: ["azure","openai","python","prompt","evaluation"]
published: false
---

## ✍️ TL;DR
- 今日の到達点：プロンプト改善の効果を **定量評価** して可視化できた  
- 学び：
  - JSONLテストセットを作って簡易スコアリングを実施  
  - 改善版プロンプトに「必須キーワード」を含める指示を追加 → 平均スコアが 0.3 → 1.0 に向上  
  - 二次分析で「キーワード羅列」など不自然さも検証できた  
- コスト：数円程度（gpt-4o-mini × 少件数テスト）

---

## 🧭 今日のゴール
- 評価用データセットで旧/新プロンプトを比較し、**改善の効果を再現性ある形で確認する**  
- 同一の質問セットを用いることで、**モデルの揺らぎではなくプロンプト改善による違い**を切り分ける  
- 改善効果を **スコアと棒グラフ** で可視化し、将来の RAG / Fine-tune 評価にもつながる基盤を整える  
- 改善済みプロンプトを確定  

---

## 🔧 手順（そのまま実行可）

### PowerShell/CLI
```powershell
cd C:\dev\azure-ai-40days\day6

# 改善前後プロンプトを評価（API呼び出し & CSV/グラフ出力）
python .\eval_prompts.py

# 結果の二次分析（自然さ/羅列疑惑/重なり度）
python .\analyze_day6.py
```

---

## 🧪 スクリプト概要（`eval_prompts.py` / `analyze_day6.py`）

### `eval_prompts.py`（評価・可視化・成果物作成）
- **目的**：旧/新プロンプトを同一テストセットで比較し、CSVと棒グラフを出力  
- **主な処理**  
  - `.env` を `python-dotenv` で読み込み → `AzureOpenAI` クライアント生成  
  - `testset.jsonl` を **`encoding="utf-8-sig"`** で読込（BOM対策）  
  - 各サンプルに対し **Base/Improved** 両プロンプトで回答  
  - **スコア関数**：`keywords` に含まれる各語の **完全一致率**  
  - 出力：`results_day6.csv`、`../articles/images/day6/prompt_compare.png`  

### `analyze_day6.py`（二次分析／健全性チェック）
- **目的**：結果CSVを読み、**不自然な羅列**や**内容一致**をざっくり検査  
- **主な指標**  
  - 文字数（極端に短いのに全キーワード一致＝羅列疑惑）  
  - `expected` と生成文の **Jaccard係数**（語彙の重なり度）  
- **今回の所見**：`Suspicious: none` → **キーワード詰め込み無し**／`jaccard` は0.0だったため、`expected` の作りや分かちが弱い可能性。必要なら **形態素解析（MeCab等）** か **埋め込み類似度**へ発展。

---

## 📐 プロンプトの変更内容

### 改善前（Base Prompt）
```python
BASE_SYS = "あなたは端的に答えるアシスタントです。"
BASE_USER_TMPL = "質問: {q}\n要点だけ短く答えて。"
```
**特徴:** 制約が弱く、短いが要点語が抜けがち。

### 改善後（Improved Prompt）
```python
IMPROVED_SYS = (
    "あなたはAzure AI学習者向けの日本語アシスタントです。"
    "回答は1〜2文で簡潔に、自然な日本語で。"
    "質問に固有の重要語を省略せず、指定されたキーワードを最低1回はそのまま含めてください。"
    "不要な前置きや婉曲表現は禁止。"
)

IMPROVED_USER_TMPL = (
    "次の質問に1〜2文で答えてください。"
    "必ず次のキーワードを最低1回以上含めること: {keywords}\n"
    "質問: {q}"
)

```

## 🔍 改善後プロンプトをこの形にした理由
- **1〜2文に制限**：冗長化を抑え、比較とコストを最適化  
- **必須キーワードを明示**：要点語の欠落を防ぎ、評価指標（完全一致率）を底上げ  
- **自然な日本語・羅列禁止**：強制に伴う**単語並べ**の副作用を抑止  
- **対象読者の明示（学習者）**：無駄な前置きを減らし、実務的な密度を確保  

---

## ✅ 検証結果
- Base Avg: **0.300**  
- Improved Avg: **1.000**  
- `results_day6.csv` と `prompt_compare.png` を保存  
- `analyze_day6.py` → 「Suspicious: none」  

<!-- スクショ: eval_prompts.py 実行後のターミナル出力（例：eval_output.png） -->
![実行後のターミナル出力](/images/day6/eval_output.png)

![比較グラフ](/images/day6/prompt_compare.png)
<!-- スクショ: prompt_compare.png の棒グラフ（必須） -->

<!-- スクショ: results_day6.csv をVS Codeで開いた画面（例：csv_view.png） もしくは analyze_day6.py の出力（例：analyze_output.png） -->
![analyze_day6.py の出力](/images/day6/analyze_output.png)

---

## 🔍 得られた考察
- 必須キーワード制約は **「指示遵守」** を強化し、今回の簡易指標では **明確に改善**  
- 一方で評価は「完全一致」依存のため、**表記ゆれに弱い**  
- 今後は **テストセット拡充（5→20→50件）** と **指標の多様化（類似度・人手評価）** で頑健性を高める  

---

## 🧯 つまずき＆対処
| エラー/症状 | 原因 | 対処（優先度順） |
|---|---|---|
| `JSONDecodeError: Unexpected UTF-8 BOM` | PowerShellのOut-FileがBOM付き保存 | `encoding="utf-8-sig"` で読込 or BOMなしで保存 |
| `401 Unauthorized` | KEY/ENDPOINT/DEPLOYMENT不一致 | .envの値・デプロイ名をAzure Portalで再確認 |
| 不自然な回答（語羅列） | 制約が強すぎる | 「自然な文」「箇条書き禁止」「反復上限」を追記 |

---

## 💰 コストメモ
- 概算：`(件数 × 2案 × (入出力トークン)) × 単価`  
- 削減策：小さなサンプルから始め、**miniモデル**／**2文制約**／**低温度(0.1)**

---

## 📌 やったこと振り返り
1. JSONLテストセットを作成  
2. `eval_prompts.py` で旧/新プロンプトを比較（CSV/グラフ出力）  
3. `analyze_day6.py` で不自然さ・重なり度を二次分析  
4. 改善案プロンプトが **定量的に優位** と確認  
5. 指標の限界と次の改善方向（類似度・人手評価）を整理  

---

## 🔮 次回の予告
Day7では **Azure Functions + SignalR** を使い、OpenAI応答をリアルタイム配信する「API連携」に進みます 🚀

---

## 📚 参考リンク
- [Azure OpenAI Service ドキュメント](https://learn.microsoft.com/azure/cognitive-services/openai/)  
- [Python dotenv](https://pypi.org/project/python-dotenv/)  
- [Prompt engineering best practices (MS Learn)](https://learn.microsoft.com/azure/ai-services/openai/concepts/prompt-engineering)  
