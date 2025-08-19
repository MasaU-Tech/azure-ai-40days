### Day7 Note

#### ✅ 成功した手順
1. **プロジェクト準備**
   ```powershell
   cd C:\dev\azure-ai-40days\
   .\.venv\Scripts\Activate.ps1
   mkdir .\day7\functions-openai-proxy -Force
   cd .\day7\functions-openai-proxy
   func init . --python
   func new --name chat --template "HTTP trigger" --authlevel "anonymous"
   pip install azure-functions "openai>=1.40.0"
   pip freeze > requirements.txt
   ```

2. **local.settings.json の編集**
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "UseDevelopmentStorage=true",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "AZURE_OPENAI_ENDPOINT": "https://<your-resource>.openai.azure.com/",
       "AZURE_OPENAI_DEPLOYMENT": "gpt4o-mini-chat",
       "OPENAI_API_VERSION": "2024-07-18",
       "SYSTEM_PROMPT": "あなたは日本語で簡潔に答えるアシスタントです。常に日本語で1文で回答してください。"
     }
   }
   ```

3. **function_app.py の編集**
   - エンドポイントの strip + 末尾 `/` 補正を追加
   - HttpResponse に `charset=utf-8` を追加

4. **環境変数の設定**
   ```powershell
   $env:AZURE_OPENAI_API_KEY = "<your-azure-openai-key>"
   ```

5. **関数の起動**
   ```powershell
   func start
   ```

6. **テスト実行（PowerShellでUTF-8設定済み）**
   ```powershell
   [Console]::OutputEncoding = [Text.Encoding]::UTF8
   $OutputEncoding = [Text.Encoding]::UTF8

   $body = @{ prompt = "あなたは自己紹介を日本語で1文で返してください。" } | ConvertTo-Json
   $res = Invoke-RestMethod -Method Post `
     -Uri "http://localhost:7071/api/chat" `
     -ContentType "application/json; charset=utf-8" `
     -Body $body
   $res | ConvertTo-Json -Depth 6
   $res.answer
   ```

#### 📄 実行ログ抜粋
```json
{
    "answer":  "私はあなたの質問に答えるためのAIアシスタントです。",
    "model":  "gpt4o-mini-chat",
    "usage":  {
                  "prompt_tokens":  53,
                  "completion_tokens":  17,
                  "total_tokens":  70
              }
}
```

#### 🎯 振り返り
- Functions 経由で JSON 応答を取得できた。
- 日本語の応答を返すために **SYSTEM_PROMPT** と **UTF-8 設定** が有効だった。
- `AZURE_OPENAI_ENDPOINT` の改行混入に注意（strip + 末尾補正で解決）。
- PowerShell は `chcp 65001` + `OutputEncoding=UTF8` が必須。

