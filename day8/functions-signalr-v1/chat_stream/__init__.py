import os, json, requests
from dotenv import load_dotenv
from openai import AzureOpenAI
import azure.functions as func

load_dotenv(r'C:\dev\azure-ai-40days\.env')

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_KEY'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

def main(req: func.HttpRequest) -> func.HttpResponse:
    data = req.get_json() if req.get_body() else {}
    prompt = data.get('prompt') or req.params.get('prompt') or '日本語で自己紹介して'
    base = os.getenv('FUNCTIONS_BASE_URL', 'http://localhost:7082')
    bcast = f'{base}/api/broadcast'

    stream = client.chat.completions.create(
        model=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt4o-mini-chat'),
        stream=True,
        messages=[{'role':'user','content': prompt}]
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else None
        if delta:
            try: requests.post(bcast, json={'message': delta}, timeout=5)
            except Exception: pass

    requests.post(bcast, json={'message': '\n\n✅ 完了'}, timeout=5)
    return func.HttpResponse(json.dumps({'ok': True}), mimetype='application/json')
