---
title: "Azure OpenAI 40日チャレンジ Day2 — Prompt Flowからgpt-4o-miniを呼び出す"
emoji: "⚡"
type: "tech"
topics: ["azure", "openai", "promptflow", "python", "gpt4o"]
published: true
---

## ✍️ TL;DR
- Prompt FlowでAzure OpenAIを呼び出すには、`@tool` 関数と辞書形式YAMLが必須
- `outputs` には `reference:` を使い、ノード名＋`.output` を指定
- 動作確認は `pf flow test --flow .` でOK

---

## 🧭 今日のゴール
- Prompt Flow から Azure OpenAI (gpt-4o-mini) を呼び出せるようにする
- YAML 形式のフロー定義 (`flow.dag.yaml`) と Python ツール (`flow.py`) の構成を理解する

---

## 🔧 手順（そのまま実行可）

### 1. ディレクトリ準備
```powershell
mkdir day2
cd day2
```

### 2. `.env` の配置
Day1で使用した `.env` をコピー
```powershell
Copy-Item ..\day1\.env .\
```

### 3. Pythonツールファイル作成（flow.py）
```python
# flow.py - Prompt FlowからAzure OpenAIを呼び出す関数を定義

# Azure OpenAI SDK（openaiパッケージ）をインポート
from openai import AzureOpenAI
import os
from promptflow.core import tool  # 推奨のimport方法
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
def ask_gpt4o(prompt: str) -> str:
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
    return resp.choices[0].message.content # 文字列1つを返す
```

### 4. フロー定義ファイル作成（flow.dag.yaml）
```yaml
# flow.dag.yaml - Prompt Flowのフローモデル設定ファイル

nodes:
  - name: gpt_answer         # ノード名（任意）
    type: python             # 実行タイプ（Python関数）
    source:
      path: flow.py          # 関数定義ファイル
      function: ask_gpt4o    # 実行する関数名
    inputs:
      prompt: ${inputs.user_input}  # ユーザー入力を関数の引数に渡す

# ← ここは辞書（マップ）形式にする
inputs:
  user_input:
    type: string
    default: "Prompt FlowからAzure OpenAIを呼び出せた？"

# ← ここも辞書（マップ）形式にする
outputs:
  answer:
    type: string
    reference: ${gpt_answer.output}  # gpt_answerノードの結果を出力に設定
```

### 5. 動作テスト
```powershell
pf flow test --flow .
```

---

## ✅ 検証チェック

- 実行結果で `answer` に日本語応答が含まれる  
- 例：
```json
{
    "answer": "はい、Prompt FlowからAzure OpenAIを呼び出すことが可能です..."
}
```

![pf flow test 結果スクリーンショット](/images/day2/pf_flow_test_result.png)

---

## 🧯 つまずき＆対処

- `NoToolDefined` → `@tool` デコレーターを付与し、関数が1つだけになるよう修正
- `EmptyOutputReference` → `outputs` 定義で `value:` ではなく `reference:` を使用
- `CommentedSeq object has no attribute 'items'` → `inputs`/`outputs` をリスト形式ではなく辞書形式に修正

---


---

## 📌 Day2のやったこと振り返り

Day2では、Azure OpenAIを**Prompt Flow経由で呼び出す**ことを実現しました。
具体的には以下のステップを踏みました。

1. **環境準備**
   - `day2/` ディレクトリを作成
   - Day1の `.env` をコピーしてAPIキーやエンドポイントを再利用

2. **Pythonツール作成**
   - `flow.py` に `@tool` 関数 `ask_gpt4o()` を実装
   - Azure OpenAI SDK経由でgpt-4o-miniに質問を投げる処理を記述

3. **フロー定義（YAML）作成**
   - `flow.dag.yaml` に nodes/inputs/outputs を辞書形式で定義
   - outputsには `reference: ${ノード名.output}` を指定

4. **エラー対応**
   - YAML形式エラー（`CommentedSeq`） → 辞書形式に修正
   - `NoToolDefined` → `@tool` を付与、関数を1つに限定
   - `EmptyOutputReference` → `outputs` の参照方法を修正

5. **動作確認**
   - `pf flow test --flow .` 実行で `answer` にモデル応答を取得
   - 実際に日本語での応答を得られ、成功を確認

---

## 💰 コストメモ
- 今回の実行は1回の呼び出しあたり数十トークン程度でごく低コスト
- 削減策：デフォルト入力の短縮、モデルを `gpt-4o-mini` 維持
---

## 🔮 次回の予告
Day3では Prompt Flow の入力を外部ファイル（CSV）から読み込み、
複数の質問を一括処理できるようにします。
さらに、Azure OpenAI の応答を整形して出力ファイルに保存する方法も実装予定です。

---

## 📚 参考リンク
- [Prompt Flow 公式ドキュメント](https://learn.microsoft.com/azure/ai-services/prompt-flow/overview)
- [Azure OpenAI Service ドキュメント](https://learn.microsoft.com/azure/ai-services/openai/)
- [Zenn CLI ガイド](https://zenn.dev/zenn/articles/install-zenn-cli)
- [GitHub Actions でZenn自動デプロイ](https://zenn.dev/zenn/articles/github-actions-auto-deploy)
