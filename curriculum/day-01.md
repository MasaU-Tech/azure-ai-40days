# Day 1: Azure OpenAI リソース作成と最小API呼び出し

## ゴール
- Azure OpenAI リソースを作成し、エンドポイント/キーを取得
- PythonからChat API最小呼び出し（1問1答）

## 前提
- Windows 11, PowerShell, VS Code
- Azureサブスクリプションあり

## 手順（要約）
1) Azure にサインイン → サブスクリプション確認  
2) Azure OpenAI リソース作成（従量課金/Standardを選ぶ）  
3) デプロイで軽量モデル（例: gpt-4o-mini）を1つ用意  
4) VS Codeで仮想環境を切って `openai` を入れる  
5) `.env` へ KEY/ENDPOINT/DEPLOYMENT を設定  
6) 最小スクリプトで 1 回問い合わせ → 応答/usage を表示  
7) コスト概算（usage を簡易計算）をメモ

## 想定つまずき
- ポータルにOpenAIが見つからない → リージョン/プレビューの有無を確認  
- PTU(固定費)を誤選択 → Standard に変更  
- 認証エラー → キー/エンドポイント/デプロイ名の取り違え
