import json
import azure.functions as func

def main(req: func.HttpRequest, signalRMessages: func.Out[func.SignalRMessage]) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        body = {}
    text = body.get("message", "")
    if text:
        signalRMessages.set([func.SignalRMessage(target="token", arguments=[text])])
    return func.HttpResponse("OK", status_code=200)
