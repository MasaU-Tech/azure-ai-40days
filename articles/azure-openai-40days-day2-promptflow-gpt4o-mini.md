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
from openai import AzureOpenAI
from dotenv import load_dotenv
from promptflow.core import tool
import os

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

@tool
def ask_gpt4o(prompt: str) -> str:
    """gpt4o-mini-chatに質問し、文字列応答を返す"""
    resp = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": "あなたは簡潔な日本語アシスタントです。"},
            {"role": "user", "content": prompt}
        ]
    )
    return resp.choices[0].message.content
```

### 4. フロー定義ファイル作成（flow.dag.yaml）
```yaml
nodes:
  - name: gpt_answer
    type: python
    source:
      path: flow.py
      function: ask_gpt4o
    inputs:
      prompt: ${inputs.user_input}

inputs:
  user_input:
    type: string
    default: "Prompt FlowからAzure OpenAIを呼び出せた？"

outputs:
  answer:
    type: string
    reference: ${gpt_answer.output}
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

## 💰 コストメモ
- 今回の実行は1回の呼び出しあたり数十トークン程度でごく低コスト
- 削減策：デフォルト入力の短縮、モデルを `gpt-4o-mini` 維持
