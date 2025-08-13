---
title: "【Azure OpenAI 40日】Day1：Azure CLIでgpt-4o-miniをJapan Eastにデプロイ"
emoji: "🚀"
type: "tech"
topics: ["Azure","OpenAI","Python","Functions","RAG"]
published: true
slug: "azure-openai-40days-day1-gpt4o-mini-cli-deploy"
---

## TL;DR
- 今日の到達点：Japan East + GlobalStandard で gpt-4o-mini (2024-07-18) をデプロイ
- 学び：
  1. モデルのバージョン（modelVersion）と API バージョンは別物
  2. Japan East では Standard SKU 非対応モデルがある → GlobalStandardで回避可能
  3. CLIだけでデプロイまで完結できる
- コスト：推定数円（84トークン / GlobalStandard 単価）

## 今日のゴール
- Azure CLIで Japan East に Azure OpenAI リソースを作成（S0 従量）
- gpt-4o-mini 2024-07-18 を GlobalStandard でデプロイ（gpt4o-mini-chat）
- Python SDK で 1問1答 + usage 表示まで動作確認

## 手順（最小実装付き）
```powershell
# ログインとサブスクリプション設定
az login
az account set --subscription "<SUBSCRIPTION_NAME_OR_ID>"

# プロバイダー登録
az provider register -n Microsoft.CognitiveServices

# リソースグループ & OpenAIリソース作成
$RG="rg-aoai-40days"
$LOC="japaneast"
$AOAI="aoai40days$RANDOM"
az group create -n $RG -l $LOC
az cognitiveservices account create -g $RG -n $AOAI -l $LOC --kind OpenAI --sku S0 --yes

# モデルバージョン確認（gpt-4o-miniのみ抽出）
az cognitiveservices account list-models -g $RG -n $AOAI --query "[?contains(modelName,'gpt-4o-mini')].[modelName,modelVersion]" -o table

# デプロイ（GlobalStandard）
$MODEL_NAME="gpt-4o-mini"
$MODEL_VERSION="2024-07-18"
az cognitiveservices account deployment create -g $RG -n $AOAI --deployment-name "gpt4o-mini-chat" --model-format OpenAI --model-name $MODEL_NAME --model-version $MODEL_VERSION --sku-name "GlobalStandard" --sku-capacity 1

# エンドポイントとキー取得（.env用）
az cognitiveservices account show -g $RG -n $AOAI --query "properties.endpoint" -o tsv
az cognitiveservices account keys list -g $RG -n $AOAI -o jsonc
````

```python
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
```

## 検証結果

```plaintext
Azure CLIを使ってOpenAIのリソースを作成し、設定を行い、デプロイするには、`az deployment create` コマンドを利用します 。
[usage] prompt=44 completion=40 total=84
```
![Python実行結果](/images/day1/python_usage_result.png)


## つまずき＆解決

* `(InvalidResourceProperties) The specified SKU 'Standard' ... not supported ... 'japaneast'`
  → Japan East では Standard 非対応 → `--sku-name GlobalStandard` に変更
* `ModuleNotFoundError: No module named 'openai'`
  → 仮想環境を有効化し、`pip install "openai>=1.35.0" python-dotenv` を実行

## コストメモ

* 概算： `(prompt_tokens/1e6)*入力単価 + (completion_tokens/1e6)*出力単価`
* 削減策：
  - モデルは mini 系を優先
  - 履歴を短くする
  - 同じ質問はキャッシュ利用

## 次回の予告

* Day2は Prompt Flow で CLI & Python 呼び出しを自動化

## 参考

* [Azure OpenAI Service documentation](https://learn.microsoft.com/azure/ai-services/openai/)
