# Day 2: Chat Completions のストリーミングと使用量ログ

## ゴール
- PythonでAzure OpenAIのChat APIを**stream=True**で受信
- `usage` をログに残し**概算コスト**を算出

## 手順
1) venv 有効化 & 依存
```powershell
cd C:\dev\azure-ai-40days\day2
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install openai python-dotenv
app.py（最小）

python
コピーする
編集する
import os, sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY"))
model = os.getenv("AZURE_OPENAI_DEPLOYMENT")

stream = client.chat.completions.create(
    model=model,
    stream=True,
    messages=[
        {"role":"system","content":"日本語で簡潔に。"},
        {"role":"user","content":"箇条書きでPythonのvenv作成手順を教えて"}
    ],
)
text=""
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
        piece = chunk.choices[0].delta.content
        print(piece, end="", flush=True)
        text += piece
print("\n---")

# 同一内容を非ストリームで投げてusage取得（概算用）
res = client.chat.completions.create(model=model, messages=[
    {"role":"system","content":"日本語で簡潔に。"},
    {"role":"user","content":"箇条書きでPythonのvenv作成手順を教えて"}
])
u = res.usage
print(f"[usage] prompt={u.prompt_tokens}, completion={u.completion_tokens}")
コスト概算式（GPT-4o mini）
(prompt_tokens/1e6 * 0.15) + (completion_tokens/1e6 * 0.60) [USD]。 
OpenAI

検証
ストリームで逐次出力が流れること

usageが数値で出ること

つまずき
401/404 → キー/エンドポイント/デプロイ名再確認

429 → リトライ＆プロンプトを短く

次回予告
画像生成API（DALL·E / GPT-Image-1）