import json, os, logging
import azure.functions as func
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_version=os.environ.get("OPENAI_API_VERSION", "2024-07-18"),
)

SYSTEM_DEFAULT = "You are a helpful assistant."

def _build_messages(prompt, messages):
    if isinstance(messages, list) and messages:
        return messages
    return [
        {"role": "system", "content": os.getenv("SYSTEM_PROMPT", SYSTEM_DEFAULT)},
        {"role": "user", "content": prompt or "こんにちは！"},
    ]

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json(silent=True) or {}
    except ValueError:
        body = {}

    prompt = body.get("prompt") or req.params.get("prompt")
    messages = _build_messages(prompt, body.get("messages"))
    temperature = float(body.get("temperature", 0.2))
    model = os.environ.get("AZURE_OPENAI_DEPLOYMENT")

    try:
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature
        )
        msg = resp.choices[0].message
        usage = getattr(resp, "usage", None)
        data = {
            "answer": getattr(msg, "content", ""),
            "role": getattr(msg, "role", "assistant"),
            "model": model,
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
        }
        return func.HttpResponse(
            json.dumps(data, ensure_ascii=False),
            headers={"Content-Type": "application/json"},
            status_code=200,
        )
    except Exception as e:
        logging.exception("chat error")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            headers={"Content-Type": "application/json"},
            status_code=500,
        )
