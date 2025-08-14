# flow.py - Prompt FlowからAzure OpenAIを呼び出す関数を定義

# Azure OpenAI SDK（openaiパッケージ）をインポート
from openai import AzureOpenAI
import os
from promptflow.core import tool  # 推奨のimport
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
# 必要なキー:
#   AZURE_OPENAI_ENDPOINT
#   AZURE_OPENAI_KEY
#   AZURE_OPENAI_DEPLOYMENT
#   AZURE_OPENAI_API_VERSION
load_dotenv()

# AzureOpenAIクライアントを初期化
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),  # エンドポイントURL
    api_key=os.getenv("AZURE_OPENAI_KEY"),              # APIキー
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")   # APIバージョン（例: 2024-07-18）
)

@tool # ★このデコレーターを付けることで「ツール」として認識される
def ask_gpt4o(prompt: str) -> dict:
    """
    Azure OpenAI (gpt4o-mini-chat) に質問を送り、応答テキストを返す関数
    - prompt: ユーザーからの質問文
    - 戻り値: モデルの応答（文字列）
    """
    resp = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # デプロイ名
        messages=[
            # システムメッセージ（AIの振る舞いを定義）
            {"role": "system", "content": "あなたは簡潔な日本語アシスタントです。"},
            # ユーザーメッセージ（質問内容）
            {"role": "user", "content": prompt}
        ]
    )
    # 最初の応答メッセージの本文を返す
    return {
        "user_input": prompt,  # ★質問を出力側に含める
        "answer": resp.choices[0].message.content
    }