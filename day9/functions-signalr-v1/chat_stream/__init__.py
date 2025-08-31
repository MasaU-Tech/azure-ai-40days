import os, json, time
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
import azure.functions as func
import httpx

# ルートの .env を読み込む（必要に応じてパス調整）
load_dotenv(r"C:\dev\azure-ai-40days\.env")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-07-18"),
    timeout=httpx.Timeout(connect=10.0, read=180.0, write=180.0, pool=180.0),
    max_retries=2,
)

# keep-alive を効かせるためにセッション使い回し
_session = requests.Session()

def _broadcast(text: str, base: str, timeout: float = 10.0):
    url = f"{base.rstrip('/')}/api/broadcast"
    try:
        _session.post(url, json={"message": text}, timeout=timeout)
    except Exception:
        # 送信失敗はユーザー体験優先で握りつぶす（必要ならログへ）
        pass

def main(req: func.HttpRequest) -> func.HttpResponse:
    data = req.get_json() if req.get_body() else {}
    prompt = (data.get("prompt") or req.params.get("prompt") or "日本語で自己紹介して").strip()
    base = os.getenv("FUNCTIONS_BASE_URL", "http://localhost:7083").rstrip("/")
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt4o-mini-chat")  # ←あなたのデプロイ名に合わせる
    max_tokens = int(os.getenv("MAX_TOKENS", "512"))

    # 50ms ごとにまとめて送るバッファ
    buf = []
    last = time.monotonic()

    def flush(force=False):
        nonlocal buf, last
        if buf and (force or time.monotonic() - last >= 0.05):
            _broadcast("".join(buf), base)
            buf.clear()
            last = time.monotonic()

    try:
        # ストリーミング本体
        with client.chat.completions.stream(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        ) as stream:
            for event in stream:
                if event.type == "content.delta":
                    delta = event.delta or ""
                    if delta:
                        buf.append(delta)
                        flush()
                elif event.type == "error":
                    _broadcast(f"\n[エラー] {event.error}\n", base)
                    break

        # 残りを吐き出して完了マーク
        flush(force=True)
        _broadcast("\n\n✅ 完了", base)
        return func.HttpResponse(json.dumps({"ok": True}), mimetype="application/json", status_code=202)

    except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError, httpx.WriteError):
        # フォールバック：非ストリーミングで最終結果だけ送る
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            text = (resp.choices[0].message.content or "")
            _broadcast(f"\n[接続が不安定のためフォールバック]\n{text}", base)
        except Exception as e2:
            _broadcast(f"\n[エラー] フォールバック失敗: {e2}\n", base)
        return func.HttpResponse(json.dumps({"ok": True, "fallback": True}), mimetype="application/json", status_code=202)

    except Exception as e:
        _broadcast(f"\n[エラー] 予期せぬ例外: {e}\n", base)
        return func.HttpResponse(json.dumps({"ok": False, "error": str(e)}), mimetype="application/json", status_code=500)
