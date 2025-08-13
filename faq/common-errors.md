# よくあるエラーと対処
- 401 Unauthorized: キー/エンドポイント/デプロイ名のミス。環境変数または.envを再確認。
- 429 Too Many Requests: レート制限。数秒スリープして再試行、トークン量を減らす。
- 404 Not Found: デプロイ名の typo。ポータルのデプロイ名と一致させる。
- SSL/Proxy関連: 企業ネットワーク下はプロキシ設定をPowerShell/requestsに。
