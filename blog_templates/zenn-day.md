---
title: "Azure OpenAI 40日チャレンジ DayX — <短い要約>"
emoji: "🚀"
type: "tech"
topics: ["azure","openai","python","promptflow","rag"]
published: false
# slug は 12〜50 文字・小文字英数字・ハイフン/アンダースコアのみ
# 例: azure-openai-40days-dayx-<topic>
slug: "azure-openai-40days-dayx-topic"
---

## ✍️ TL;DR
- 今日の到達点：<一文>
- 学び：<3点を箇条書き>
- コスト：<推定¥ / 実測¥>（モデル/回数）

---

## 🧭 今日のゴール
- <1–3個の箇条書きで具体的に>

---

## 🔧 手順（そのまま実行可）

### PowerShell/CLI
```powershell
# 実行コマンドを最小で、コメント付きで
```

### Python（最小実装）
```python
# 20〜40行程度の最小例。環境変数は .env を使用
```

> 補足：危険/高コスト操作がある場合は、ここに **⚠️注意** を先に明記。

---

## ✅ 検証結果
- 何が表示されればOKか（ログ/画面/応答例）
- 画像（任意）: `images/dayX/<screenshot.png>` を相対パスで
![screenshot](../images/dayX/screenshot.png)

---

## 🧯 つまずき＆対処
| エラー/症状 | 原因 | 対処（優先度順） |
|---|---|---|
| `401 Unauthorized` | KEY/ENDPOINT/DEPLOYMENTミス | 1) .env再確認 → 2) Portalでデプロイ名を再確認 |
| `EmptyOutputReference` | YAMLのoutputs参照方法誤り | `reference: ${node.output}` に修正 |
|  |  |  |

---

## 💰 コストメモ
- 概算の式：`(prompt/1e6)*入力単価 + (completion/1e6)*出力単価`
- 削減策：モデルmini優先／プロンプト短縮／キャッシュ／バッチ化
- usageログをCSVに追記して日次合計を可視化

---

## 📌 やったこと振り返り
1. <手順の要点1>
2. <要点2>
3. <要点3>

---

## 🔮 次回の予告
- <DayX+1 の到達点や準備>

---

## 📚 参考リンク
- <公式ドキュメントへのリンク>
- <関連記事>
