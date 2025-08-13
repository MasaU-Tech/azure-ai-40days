# day1_min.py — Azure OpenAI 最小利用例（解説付き）
# -------------------------------------------------------
# このスクリプトは Azure OpenAI (gpt-4o-mini) に 1問1答を送り、
# 応答とトークン使用量(usage)を表示します。

from openai import AzureOpenAI   # Azure OpenAI 用クライアントクラス
from dotenv import load_dotenv   # .envファイル読み込み用
import os, sys

# .env ファイルを読み込む（環境変数として反映）
load_dotenv()

# 必須環境変数が設定されているか確認
need = [
    "AZURE_OPENAI_ENDPOINT",     # Azure OpenAI リソースのエンドポイントURL
    "AZURE_OPENAI_KEY",          # APIキー
    "AZURE_OPENAI_DEPLOYMENT",   # デプロイ名（CLIで作成した gpt4o-mini-chat）
    "AZURE_OPENAI_API_VERSION"   # APIバージョン（例: 2024-02-15-preview）
]
missing = [k for k in need if not os.getenv(k)]
if missing:
    print("環境変数が不足:", ", ".join(missing))
    sys.exit(1)  # 足りない場合は終了

# AzureOpenAI クライアントを初期化
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),  # エンドポイント
    api_key=os.getenv("AZURE_OPENAI_KEY"),              # APIキー
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")   # APIバージョン
)

# Chat Completions API を呼び出す
# - model は deployment name を指定
# - messages は会話の履歴（role: system/user/assistant）
resp = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "あなたは簡潔で正確な日本語アシスタントです。"},
        {"role": "user", "content": "Azure CLIだけでOpenAIをデプロイする方法を一言で？"}
    ]
)

# 応答本文（最初の候補）を表示
print(resp.choices[0].message.content)

# トークン使用量を取得して表示
# prompt_tokens: 入力に使ったトークン数
# completion_tokens: 出力に使ったトークン数
# total_tokens: 合計トークン数
u = resp.usage
print(f"[usage] prompt={u.prompt_tokens} completion={u.completion_tokens} total={u.total_tokens}")
