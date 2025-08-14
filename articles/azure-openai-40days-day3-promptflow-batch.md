# Azure OpenAI 40 Days Challenge - Day3
## TL;DR
- Day3では **Prompt Flowのバッチ実行** と **結果のCSV化** を行った  
- 実行データから質問と回答をペアにして可視化  
- PowerShell と `flow.py` 修正版でつまづきを解消  

---

## 今日のゴール
- Prompt Flowで複数の質問を一括処理
- 出力結果をCSVに変換
- 変換スクリプトの再利用

---

## 1. 今日やったこと
1. **Prompt Flowでバッチ処理**
   - `pf run create` を使い、複数の質問を一括処理  
   - 入力は CSV（`questions.csv`）を使用し、`user_input` 列にマッピング  
2. **実行結果の取得**
   - `outputs.jsonl` を元に `flow_outputs.jsonl` を作成  
   - PowerShell で JSONL をパースして `answers.csv` に変換  
3. **flow.py の修正**
   - 出力フォーマットを改善し、`question` と `answer` が正しく抽出されるように調整  

---

## 2. つまづき & 対処
### (1) JSONL 読み込み時の文字化け
- **原因**: PowerShell が UTF-16 で読み込んでいた  
- **対処**: `-Encoding UTF8` を指定して正しくパース  

```powershell
Get-Content .\flow_outputs.jsonl -Encoding UTF8 | 
  ForEach-Object {
    $o = $_ | ConvertFrom-Json
    [PSCustomObject]@{
      question = $o.inputs.user_input
      answer   = $o.outputs.answer
    }
  } | Export-Csv .\outputs\answers.csv -NoTypeInformation -Encoding UTF8
```

---

### (2) flow.py 出力の不整合
- **原因**: 出力ノードのキー名と YAML 側の設定が一致していなかった  
- **対処**: ノード定義の `outputs` 部分を修正し、`answer` を正しく返すよう変更  

---

## 3. 検証結果
- Prompt Flow バッチ実行画面
![](/image/day3/run_batch.png)  
- `answers.csv` の先頭数行（質問と回答が並んでいる部分）  
![](/image/day3/answers.png)  
---

## 4. Day3のやったこと振り返り
Day3では、Prompt Flowを使って**複数の質問を一括処理（バッチ実行）**し、その結果を**CSV形式で保存**する流れを確立しました。  
特に重要だったのは以下の3点です。

1. **バッチ実行のパラメータ理解**  
   `--data` で入力ファイルを指定し、`--column-mapping` でフローに渡すカラムをマッピングする必要がある。

2. **出力ファイル形式の理解**  
   Prompt FlowはJSON Lines形式(`outputs.jsonl`)で結果を出すため、単純にExcelで開けない。Pythonでの変換が必須。

3. **実務的な落とし穴の回避**  
   PowerShellの既定文字コード（utf-16）が原因での文字化け、CSVの列名ミス、実行名の重複エラーなどを体験的に解消。

このプロセスを確立したことで、Day4以降のRAG構成や外部データ連携にもスムーズに進める下地ができました。

---

## 5. 次回予告
Day4では  
- 生成結果の精度評価（評価フローの作成）  
- メトリクス出力と可視化  
を予定  

---

## 6. 参考情報
- [Prompt Flow 公式ドキュメント](https://learn.microsoft.com/azure/ai-services/promptflow/)
- [PowerShell ConvertFrom-Json ドキュメント](https://learn.microsoft.com/powershell/module/microsoft.powershell.utility/convertfrom-json)
- [Azure OpenAI サービス概要](https://learn.microsoft.com/azure/cognitive-services/openai/overview)
