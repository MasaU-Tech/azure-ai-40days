import json
import azure.functions as func

def main(req: func.HttpRequest, signalRMessages: func.Out[str]) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        body = {}
    text = body.get("message", "")

    if text:
        payload = [ { "target": "token", "arguments": [ text ] } ]
        signalRMessages.set(json.dumps(payload))

    return func.HttpResponse("OK", status_code=200)
