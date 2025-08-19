import os, json
import azure.functions as func
from openai import AzureOpenAI

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="chat", methods=["GET","POST"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    # --- ① ここを追記：エンドポイント整形（改行/空白対策＋末尾スラッシュ保証） ---
    ep = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip()
    if not ep.endswith("/"):
        ep += "/"
    # ---------------------------------------------------------------------------

    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=ep,  # ← ここを ep に変更
        api_version=os.environ.get("OPENAI_API_VERSION", "2024-07-18"),
    )

    try:
        body = req.get_json()
    except ValueError:
        body = {}

    prompt = body.get("prompt") or req.params.get("prompt") or "こんにちは！"
    messages = [
        {"role":"system","content": os.getenv(
            "SYSTEM_PROMPT",
            "あなたは日本語で簡潔に答えるアシスタントです。常に日本語で1文で回答してください。"
        )},
        {"role":"user","content": prompt},
    ]

    resp = client.chat.completions.create(
        model=os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        messages=messages,
        temperature=float(body.get("temperature",0.2))
    )
    usage = getattr(resp, "usage", None)

    data = {
        "answer": resp.choices[0].message.content,
        "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        "usage": {
            "prompt_tokens": getattr(usage,"prompt_tokens",None),
            "completion_tokens": getattr(usage,"completion_tokens",None),
            "total_tokens": getattr(usage,"total_tokens",None),
        },
    }

    # --- ② ここを追記：charset=utf-8 を明示して文字化け防止 ---
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Type": "application/json; charset=utf-8"},
        status_code=200
    )
