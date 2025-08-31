---
title: "【Azure OpenAI 40日】Day9：履歴・送信中インジケーター・吹き出しでUXを仕上げる"
emoji: "💬"
type: "tech"
topics: ["azure","openai","javascript","signalr","frontend"]
published: true
---

> Windows 11 / PowerShell / VS Code 前提。ローカル実行でUXを一気に底上げします。Day8のリアルタイム配信（Functions + SignalR）を **そのまま流用** し、フロントだけ賢くします。

## ✍️ TL;DR
- **今日の到達点**：Functions+SignalR を活かしたチャットUIで **履歴・送信中・吹き出し** を実装し、Day9(7083) 環境で安定稼働。
- **学び**：1) localStorageで状態永続化 2) SignalRストリーミングを**50msバッファ**で安定化 3) SDK **timeout/フォールバック**設計。
- **コスト**：ローカルは **¥0**。実API時は `入力/出力トークン ÷ 1e6 × 単価` で見積り（miniモデル推奨）。

---

## 🧭 今日のゴール
- 会話履歴を **localStorage** で保持
- **送信中インジケーター** と **接続ステータス** を表示
- Day8の **negotiate/chat_stream/broadcast** を流用し最小で実装

## 🎯 目的と背景（Day9）
- **目的**: UXを意識したUI作りを学ぶ。
- **背景**: 技術力だけでなく「使いやすさ」が評価される。小さな改善が習慣化のきっかけになる。

> Day8 のゴール「ローカルでのリアルタイム配信」から一歩進め、**使える**UIに仕上げるのがDay9の狙いです。

---


## 前提
- Day8 の Functions プロジェクト（`negotiate` / `chat_stream` / `broadcast`）がローカルにある
- Day9 用として Day8 を **フォルダごと複製** 済み（例：Day9は **ポート 7083** で起動）
- フロントは `day9/web-clean-plus/index.html`（HTML単体）

---

## 🔧 手順（そのまま実行可）

### PowerShell/CLI
```powershell
# 1) Day9 Functions を 7083 で起動
cd C:\dev\azure-ai-40days\day9\functions-signalr-v1
func start --port 7083 --cors "*"

# 2) フロントを 5509 で配信
cd C:\dev\azure-ai-40days\day9\web-clean-plus
python -m http.server 5509

# 3) ブラウザ表示
Start-Process "http://127.0.0.1:5509/index.html"
```

### Python（最小実装）
> ストリーミングはSignalRで受けるため、HTTP応答は 200/202 を確認できればOK。
```python
# FILE: day9/test_day9_client.py
import requests
BASE = "http://localhost:7083"
try:
    # 1) negotiate が 200 を返すか
    r1 = requests.post(f"{BASE}/api/negotiate", timeout=10)
    print("negotiate:", r1.status_code)

    # 2) chat_stream に短文送信
    r2 = requests.post(f"{BASE}/api/chat_stream",
                       json={"prompt":"接続確認です。1行で返答して"},
                       timeout=15)
    print("chat_stream:", r2.status_code)
    print((r2.text or "")[:120])
except Exception as e:
    print("error:", e)
```

---

## ✅ 検証結果

![初期状態](/images/day9/ui-hero.png)
_初期状態（履歴クリア直後のヒーローショット）_
- **Connected（緑ドット）** が表示される
- 送信で **送信中…** が出る → 完了で消える
- 吹き出しに **文字が少しずつ追記** される（逐次表示）
- リロード後も **履歴が残る**（localStorage）
- エラー時は左吹き出しに **`[エラー] ...`**

![Connected状態のヘッダー](/images/day9/ui-connected.png)
_Connected 状態（negotiate 成功後。ヘッダーの緑ドット）_
![送信中インジケーター](/images/day9/ui-sending.png)
_送信直後に表示される「送信中…」とドットアニメーション_
![逐次表示の途中](/images/day9/ui-streaming.png)
_AI吹き出しへ文字が徐々に追記されていく様子（ストリーミング）_
![リロード後も履歴が残る](/images/day9/ui-persistent.png)
_リロード後も履歴が残っていることを確認（localStorage）_

## 実装ポイント（フロント）
- **localStorage** で `day9-messages` を保存
- **送信中インジケーター** で待機を可視化
- **接続ステータス**（緑ドット）で SignalR の状態を表示
- **Base URL** を画面から変更・保存できる
- **Ctrl+Enter** 送信対応

> HTML1枚に集約。バックエンドのAPI構成（`/api/negotiate`→SignalR接続、`/api/chat_stream`→逐次配信）は Day8 のまま。

---

## 実装ポイント（サーバ / 安定化の差分）
長文や回線の揺れで **`RemoteProtocolError: incomplete chunked read`** が出る場合に備え、Day9では以下を追加：

- OpenAI SDK の **`timeout`**（read 180s）と **`max_retries`** を明示
- **50ms バッファリング** でトークンまとめ送信（過剰POSTを抑制）
- 例外時は **非ストリーミングにフォールバック** して完了まで届ける

> これにより「長時間ストリームでも落ちにくい」「落ちても体験を壊さない」挙動になります。

---

## 🧯 つまずき＆対処

![エラーバブル例](/images/day9/ui-error-bubble.png)
_Base URL を誤らせた際のエラーバブル例（UIが固まらない）_

| エラー/症状 | 原因 | 対処（優先度順） |
|---|---|---|
| `GET /index.html 404` | http.serverの配信ルートとURL不一致 | 1) 配信フォルダで起動 2) `--directory` 指定 3) URLを `http://127.0.0.1:5509/index.html` に |
| `TypeError: Failed to fetch` | CORS/URL/未起動 | 1) `--cors "*"` で起動 2) Base URL=`http://localhost:7083` 3) http配信で開く |
| `negotiate 404/500` | ルート/ポート違い | `Invoke-WebRequest -Method Post http://localhost:7083/api/negotiate` で単体確認 |
| `RemoteProtocolError: incomplete chunked read` | 長文＋回線揺れ／過剰POST | SDKに `timeout(read=180s)` と `max_retries`、**50msバッファ**、必要なら**非ストリーミングにフォールバック** |
| `401/403 negotiate` | 認証レベル/キー | 一時は `?code=...`、本番は `authLevel:function` や AAD/APIM を検討 |
| `broadcast 404` | 関数未配置 | Day9 プロジェクト内に `broadcast` があるか確認（Day8から複製） |

---

## コストメモ（ローカル検証）
- **概算**: `入力トークン/1e6 * 単価 + 出力トークン/1e6 * 単価`
- **節約**: `gpt-4o-mini` を優先／プロンプト短縮／UI側で連打防止／（後日）キャッシュ

---


## 検証用プロンプト（コピペ）
**① 即応（短文）**
```
1行で答えて：今日の学習の振り返り例を丁寧に。
```
**② 長文（Markdown 300〜400字）**
```
Markdownで、短時間で集中力を上げる方法を見出し＋箇条書き3点＋短い結論で300〜400字。
```
**③ カウントアップ**
```
1から50までを半角スペース区切りでゆっくり出力して。改行は入れないで。
```
**④ 表＋コード**
```
CPUとGPUの違いを2列のMarkdown表（項目/説明）で。続けてJavaScriptサンプルを```で囲って提示。
```
**⑤ XSS/記号エスケープ**
```
次の文字列をそのまま返して：<script>alert('xss')</script> & " ' < >
```
**⑥ バリッドJSONのみ**
```
必ず有効なJSONだけで返答。{"title":文字列,"bullets":[文字列3つ]}。テーマは「時間管理のコツ」。
```
**⑦ メモ→想起（2回）**
```
私のニックネームはタロウです。覚えておいて。
```
```
私のニックネームは？
```
**⑧ JA→EN 要約翻訳**
```
次の文を英語に翻訳し、15 words以内で要約して：今日はUIの改善で効率が上がった。
```
**⑨ 要点抽出（3点）**
```
以下から重要ポイントを3点に要約して：
- localStorageで履歴保持
- SignalRで逐次配信
- 送信中インジケーターで待機を可視化
```
**⑩ 危険依頼への対応**
```
危険な行為の具体手順は提供せず、代わりに一般的な安全アドバイスを短く示して。
```
**⑪ 故意エラー（確認用）**
- Base URL を `http://localhost:7099` に変更 → 任意の短文送信

**⑫ 再読み込み（永続化）**
- 任意の短文を送信 → ブラウザをリロード

---

## 📌 Day9でやったこと振り返り
1. Day8のリアルタイム配信を**流用**しつつ、UIを **履歴/送信中/吹き出し** で改善
2. ストリーミングの**安定化（timeout/バッファ/フォールバック）** を実装
3. フロントは **HTML1枚**、Base URL 切替でローカル/クラウドに向けられる

## まとめ
Day8 の実装を活かしつつ、**localStorage / 送信中表示 / 接続ステータス / 吹き出し** でUXを底上げ。長文時の切断にも **リトライ・フォールバック** で耐える作りにしました。次はこのUIを土台に **RAG（Day10）** の下準備へ。

## 🔮 次回の予告
- Day10：Azure Cognitive Search + Blob で **RAG基礎**（インデックス作成 → データ投入 → 検索テスト）

## 📚 参考リンク
- [Azure Functions（Python）開発ガイド](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure Functions ドキュメント（全般）](https://learn.microsoft.com/en-us/azure/azure-functions/)
- [Azure SignalR Service ドキュメント](https://learn.microsoft.com/en-us/azure/azure-signalr/)
- [Azure Functions の SignalR バインディング](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-signalr-service)
- [SignalR 接続情報（negotiate）入力バインディング](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-signalr-service-input)
- [OpenAI Python ライブラリ（公式）](https://platform.openai.com/docs/libraries)
- [Streaming API responses（OpenAI）](https://platform.openai.com/docs/guides/streaming-responses)
- [Chat Completions のストリーミング API 参照](https://platform.openai.com/docs/api-reference/chat/streaming)
- [Azure OpenAI 参照（Azure AI Foundry Models）](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/reference)
- [Chat Completions の使い方（Azure OpenAI）](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/chatgpt)

