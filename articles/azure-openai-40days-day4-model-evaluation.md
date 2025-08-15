---
title: "【Azure OpenAI 40日】Day4：モデル評価とメトリクスの確認"
emoji: "🔍"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["Azure", "OpenAI", "PromptFlow", "AI", "評価"]
published: true
---

## TL;DR
- **目的**: Day3 で作成したモデル回答の精度を評価
- **成果物**: `rows.csv` と `summary.csv` による詳細スコアと集計
- **結果**: 平均スコアは 0.333、閾値 0.7 に対して NG が 2件
- **学び**: 評価は正解データと出力が揃わないと成立しない。改善にはプロンプト設計や事前処理の見直しが必要

---

## 今日のゴール
- モデル回答と正解データの突き合わせによる精度評価
- NG回答の傾向把握と改善施策の足がかり作り

---

## 実施内容

### 1. 評価用データの準備
- Day3 の出力（answer）と正解データ（ground_truth）をマージ  
- CSV形式に加工し、評価フローに渡せる形式に変換
- 実際の作業例：
```powershell
mkdir outputs
Get-Content .\outputs\rows.csv -TotalCount 5
```

---

### 2. 評価フローの実行

* コマンド：

```powershell
pf run create --flow . --name $RUN --data .\eval.csv --column-mapping answer='${data.answer}' ground_truth='${data.ground_truth}' --stream
```

* モデル出力と正解を比較し、完全一致で 1.0、それ以外は 0.0 をスコアとして出力

---

### 3. 評価結果の取得

* 詳細（各質問の結果）:

```powershell
Get-Content .\outputs\rows.csv -TotalCount 5
```

例:

```
"question","answer","ground_truth","score"
"Azure OpenAIとは何ですか？","Azure OpenAIは...","Microsoft Azure上で提供されるOpenAIモデルのクラウドサービス","1.0"
...
```

* 集計（全体スコア）:

```powershell
Get-Content .\outputs\summary.csv
```

結果:

```
run,day4-eval-20250815-152329
avg_score,0.333
threshold,0.7
ng_count,2
```

---

## スクリーンショット

- pf flow test 実行成功のPowerShell出力
![](/images/day4/day4-pf-flow-test-success.png) <!-- day4-pf-flow-test-success.png -->

- pf run show-details の評価結果テーブル
![](/images/day4/day4-pf-run-show-details-table.png) <!-- day4-pf-run-show-details-table.png -->

- rows.csvとsummary.csv の内容
![](/images/day4/day4-summary-csv.png) <!-- day4-summary-csv.png -->

- day4のフォルダ構成
![](/day4-folder-structure.png) <!-- day4-rows-csv-preview.png -->

---

## つまずき＆対処

### 評価フローの入力不足エラー

* **現象**: `Required input(s) ['answer', 'ground_truth'] are missing`
* **原因**: CSVに必要カラムが揃っていなかった
* **対処**: `answer` と `ground_truth` カラムを含む評価用 CSV を事前作成

### ディレクトリ未作成エラー

* **現象**: `DirectoryNotFoundException`
* **原因**: `outputs` ディレクトリが存在しない
* **対処**: `mkdir outputs` で事前作成

### CLI引数エラー

* **現象**: `pf run show-details --format json` が認識されない
* **原因**: バージョン差異によりオプション未対応
* **対処**: 標準出力をそのままリダイレクトしてファイル保存

---

## Day4やったことの振り返り

* 評価フローのセットアップと実行
* `rows.csv` と `summary.csv` から回答精度を確認
* 評価プロセスを通じて「正解データの整備の重要性」を再認識
* モデル改善に向けた指標として「平均スコア」「NG件数」を確保

---

## 学び

* 評価は正解データとモデル出力の**粒度合わせ**が重要
* NGの多くは「言い回し・形式の違い」で発生しており、完全一致判定では弾かれる
* 閾値を下げるより、出力の正規化やプロンプト修正で改善を図るべき

---

## 次のステップ

1. NG回答の原因分析（用語・表現・フォーマット差異）
2. プロンプト修正と再評価
3. 閾値に対して安定して達成できる状態を目指す

---

## 参考情報

* [Prompt Flow公式ドキュメント - 評価機能](https://learn.microsoft.com/azure/machine-learning/prompt-flow)
* [Azure OpenAI Service 概要](https://learn.microsoft.com/azure/cognitive-services/openai/overview)