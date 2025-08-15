
# Day1 進捗まとめ

## 進捗
- Azure OpenAIリソース作成（Japan East, SKU: Global Standard, バージョン: 2024-07-18）
- .env の `AZURE_OPENAI_API_VERSION` を `2024-07-18` に更新
- Pythonスクリプト `day1_min.py` 実行成功（Azure CLIコマンド例と使用トークン数表示）
- GitHubへの初回push（articles, images も追加）
- Zenn用記事テンプレ作成・アップロード
- blogフォルダ整理（articlesへ移動）

## 作成したコードやコマンド
- Pythonコード `day1_min.py`（Azure OpenAIクライアント接続＋プロンプト送信）
- `.env` 環境設定更新
- GitHub push手順
- Zenn CLIによる記事アップロード方法

## 解決済みの課題
- `ModuleNotFoundError: No module named 'openai'` → `pip install openai` で解決
- blogフォルダとarticlesフォルダの整理
- Zennファイル名制約（12〜50文字、半角英数字・ハイフン・アンダースコア）対応

## 未解決の課題
- 特になし



# Day2 進捗まとめ

## 進捗
- Prompt Flow環境構築
- Pythonファイル・YAMLファイルに詳細コメント追加
- `pf flow test` 実行によりAzure OpenAI呼び出し成功
- GitHubへのpush（Day2作成物含む）
- Zenn記事案作成（TL;DR追加、Prompt Flowのメリット説明）

## 作成したコードやコマンド
- Flow用Pythonスクリプト（`@tool`デコレーター使用）
- flow.dag.yaml（辞書形式入力、出力`answer`参照修正）
- `pf flow test --flow .` による検証

## 解決済みの課題
- `CommentedSeq` エラー → YAML形式を辞書形式に修正
- `NoToolDefined` エラー → Pythonスクリプトに `@tool` 関数を追加
- `EmptyOutputReference` エラー → flow.dag.yamlで `outputs.answer` の参照修正

## 未解決の課題
- 特になし



# Day3 進捗まとめ

## 進捗
- バッチ実行用データ（CSV, JSONL）準備
- `pf run create` によるバッチ処理実行
- 実行結果 `flow_outputs.jsonl` が生成されないケースを確認し、`outputs.jsonl` をコピー＆リネームで対応
- PowerShellスクリプトで `answers.csv` を生成し質問と回答を突き合わせ
- flow.py修正版で再実行検証
- Zenn記事案作成（つまづき＆対処、振り返り、スクリーンショット挿入）
- GitHubへのpush（スクショ含む）

## 作成したコードやコマンド
- PowerShellでのCSV生成スクリプト（UTF-8エンコード対応）
- flow.py 修正版（入力と出力を正しくマッピング）
- `pf run create` バッチ実行コマンド
- CSV出力後の`Select-Object`による確認

## 解決済みの課題
- `Fail to load invalid data` → 入力ファイル形式をCSV/JSONLに修正
- `RunExistsError` → 実行名を変更して再実行
- `pf run download` コマンド誤用 → 正しい出力取得手順に修正
- PowerShellのUTF-16読み込み問題 → UTF-8で再エクスポート
- 質問列が空欄 → flow_outputs.jsonlの正しい解析により解決

## 未解決の課題
- flow_outputs.jsonlが生成されない根本原因の特定（暫定的にoutputs.jsonlで対応）
