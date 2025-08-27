import os, json
from openai import AzureOpenAI
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION","2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    try:
        r = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT","gpt4o-mini-chat"),
            messages=[{"role":"user","content":"ping"}],
            max_tokens=8
        )
        txt = r.choices[0].message.content
        return func.HttpResponse(json.dumps({"ok": True, "text": txt}), mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(json.dumps({"ok": False, "error": str(e)}),
                                 mimetype="application/json", status_code=500)
