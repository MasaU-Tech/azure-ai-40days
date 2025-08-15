# Day4 進捗記録

## 進捗
- **カリキュラム**：モデル評価（Model Evaluation）の実施  
- `pf flow test` 実行時のエラー（`ValueError: 'float' is not a valid ValueType` や `Required input(s) ['answer', 'ground_truth'] are missing`）を修正  
- 評価用の入力データ作成（`answer` と `ground_truth` を含むCSV）  
- 評価フローのテスト実行が正常完了  
- 評価結果（`rows.csv` と `summary.csv`）を取得  
- **Day4記事（Zenn用）** の初版を作成  
- Day4で実際に行ったことを整理し、モデル評価の流れを明確化  

---

## 作成したコードやコマンド

### 実行コマンド例
```powershell
# 評価フローのテスト
pf flow test --flow .

# 評価結果の詳細（details.json出力）
pf run show-details -n $RUN | Out-File -FilePath .\outputs\details.json -Encoding utf8

# 評価結果の行ごとのスコア
Get-Content .\outputs\rows.csv -TotalCount 5

# 評価結果のサマリー
Get-Content .\outputs\summary.csv
```

### 入力CSV例
```csv
question,answer,ground_truth
"Azure OpenAIとは何ですか？","Azure OpenAIは、MicrosoftのAzureクラウドプラットフォーム上で提供されるOpenAIの人工知能モデルへのアクセスサービスです。...","Microsoft Azure上で提供されるOpenAIモデルのクラウドサービス"
"GPT-4o-miniの特徴は？","GPT-4o-miniは、OpenAIが開発した小型の言語モデルです。その特徴には以下の点があります。...","小型で軽量、高速応答可能なOpenAIの言語モデル"
```

---

## 解決済みの課題
1. **`ValueError: 'float' is not a valid ValueType` エラー**
   - 原因：flow定義の出力型が `float` で、`ValueType` に未対応の型指定になっていた
   - 対策：`string` または `number` に修正して対応
2. **`Required input(s) ['answer', 'ground_truth'] are missing` エラー**
   - 原因：評価用のCSVに必要なカラムが不足
   - 対策：`answer` と `ground_truth` を含むCSVを作成
3. **`metrics.json` 出力時のフォルダ不存在エラー**
   - 原因：`outputs` フォルダ未作成
   - 対策：`mkdir outputs` 実行後に再試行
4. **`--format json` オプション未対応エラー**
   - 原因：CLIバージョンの仕様
   - 対策：`--format json` を削除し、PowerShellで整形

---

## 未解決の課題
- `pf run show-metrics` が `{}` を返す原因の特定（評価指標が正しく計算されていない可能性）
- モデル評価結果の解釈方法（閾値の設定やスコア分布の意味づけ）を深掘りする必要あり
