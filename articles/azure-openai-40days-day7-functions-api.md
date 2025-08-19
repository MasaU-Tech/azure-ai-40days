---
title: "Day7：Azure FunctionsでAzure OpenAIをAPI化する"
description: "Azure Functions の HTTP トリガーを使って Azure OpenAI をAPI化し、PowerShellから日本語応答を確認する手順をまとめました。"
tags: ["Azure", "OpenAI", "Python", "Serverless", "Functions"]
emoji: "⚡"
type: "tech"
topics: ["azure", "openai", "python", "serverless", "functions"]
published: true
---

## TL;DR
Azure Functions を使うと Azure OpenAI を簡単に API 化できる
- function_app.py 内で SDK を呼び出し、HTTPエンドポイント /api/chat を公開
- PowerShell から JSON 応答を取得、日本語応答を確認済み
- Day1〜6 の「ローカル実験」から Day7 で「API公開」へ進化

---

## 🧭 今日のゴール
- Azure Functions の HTTP トリガーで `/api/chat` を実装
- Azure OpenAI を SDK 経由で呼び出す
- PowerShell から呼び出し、日本語応答が返ることを確認

---

## 🎯 目的と背景
- **目的**: モデルをAPI化して、アプリや他サービスから安全に呼び出せる形にする。  
- **背景**: 実務ではスクリプト単体での利用ではなく、Functions のようなサーバーレス環境に載せることで再利用性・拡張性・監視性が高まる。後続の SignalR 連携や認証追加の基盤になる。

---

## 📘 Azure Functionsとは？
Azure Functions は Microsoft Azure が提供する **サーバーレスの関数実行サービス (FaaS)** です。サーバーやインフラを意識せず、数行〜数十行のコードをイベント駆動で動かせます。

- **イベント駆動型**: HTTPリクエスト、タイマー、キュー、Blobイベントなどをトリガーに処理を開始。
- **スケーラブル**: リクエストが増えれば自動でスケールアウト、使わなければほぼコストゼロ。
- **複数言語対応**: Python, C#, JavaScript, Java, PowerShell などで開発可能。
- **API化に便利**: 簡単にHTTPエンドポイントを公開でき、外部アプリやサービスから利用可能。

今回のDay7では、Functionsを利用して **Azure OpenAI SDK呼び出しをHTTP APIとして公開** します。
つまり「ローカルで動かすスクリプト」を「誰でも呼べるWeb API」に変換する器が Functions です。

---

## 🔧 手順

### 1. プロジェクト作成
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

![](/images/day7/powershell-init.png) 

---

### 2. local.settings.json 設定
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

---

### 3. function_app.py の編集
```python
@app.route(route="chat", methods=["GET","POST"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    ep = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip()
    if not ep.endswith("/"):
        ep += "/"

    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=ep,
        api_version=os.environ.get("OPENAI_API_VERSION", "2024-07-18"),
    )
    ...
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Type": "application/json; charset=utf-8"},
        status_code=200
    )
```

---

### 4. 環境変数の設定
```powershell
$env:AZURE_OPENAI_API_KEY = "<your-azure-openai-key>"
```

---

### 5. 起動とテスト
```powershell
func start
```
別ターミナルから:
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

![](/images/day7/powershell-success.png)

---

## ✅ 検証結果
実際の出力：
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

✅ 日本語の応答がJSON形式で返り、Day7の目標達成。

---

## 🧯 ハマりどころと解決策
- `401 Unauthorized` → キー未設定／環境変数名間違い → `$env:AZURE_OPENAI_API_KEY` 再設定
- `InvalidURL: ... '\n'` → local.settings.json に改行混入 → `.strip()` + 末尾`/`補正
- 文字化け（å·ä½…） → PowerShellをUTF-8設定 ＋ `charset=utf-8` をHttpResponseに追加

![](/images/day7/powershell-error.png)

---

## 💡 Day1〜6とDay7の違い
- **Day1〜6**: Python SDKをローカルスクリプトで直接実行。自分だけが利用できる。  
- **Day7**: Azure Functions経由で **HTTP API化**。外部アプリやユーザーもアクセス可能。  
- **進化点**: 「ローカル実験」から「公開API」へステップアップ。SDK呼び出し部分は `client.chat.completions.create(...)` が該当。  

---

## 💰 コストメモ
- **計算式**: `(入力トークン数/1e6×単価) + (出力トークン数/1e6×単価)`
- **削減策**: miniモデル優先・systemプロンプト短縮・返答長を制限・キャッシュ活用

---

## 🎯 まとめ
- Functions を使って Azure OpenAI を**API化**できた
- JSON応答を返し、PowerShellから検証成功
- 日本語で返すには **SYSTEM_PROMPT** と **UTF-8設定** が重要
- Day7は「ローカルで試す」から「HTTP APIとして外部公開」への進化のステップ

次は Day8 で **SignalR連携によるリアルタイム化**に進みます 🚀

