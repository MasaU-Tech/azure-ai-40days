import azure.functions as func

def main(req: func.HttpRequest, connectionInfo: str) -> func.HttpResponse:
    # 入力バインディングが作る {url, accessToken} をそのまま返す
    return func.HttpResponse(connectionInfo, mimetype="application/json")
