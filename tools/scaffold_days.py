# tools/scaffold_days.py
from pathlib import Path

BASE = Path(r"C:\dev\azure-ai-40days")
CURR = BASE / "curriculum"
CURR.mkdir(parents=True, exist_ok=True)

template = """# Day {num:02d}: {title}

## ゴール
- <1–3個>

## 前提
- Windows 11 / PowerShell / VS Code
- Azureサブスクリプション有効

## 手順（要約）
1) <サマリ>
2) <サマリ>
3) <サマリ>

## 想定つまずき
- `エラー…` → 原因 → 対処
"""

# 必要に応じて編集：40日の見出し（例）
titles = {
  2:"Chat Completions最小実装（usage/コスト記録）",
  3:"画像生成（最小）と保存・掲載",
  4:"音声→テキスト/テキスト→音声の最小連携",
  5:"APIラッパ＆リトライ/レート制御",
  6:"プロンプト基礎（指示の具体化/制約/例示）",
  7:"system/few-shot設計と日本語/英語比較",
  8:"Prompt flow導入（サンプル実行）",
  9:"Prompt flowで評価（正答率/長さ）",
 10:"プロンプト自動バリアント比較",
 11:"改善事例まとめ（Before/After）",
 12:"復習・保留消化",
 13:"Functionsプロジェクト作成（HTTP）",
 14:"SignalR準備（Free枠）",
 15:"チャットUI最小（HTML/JS）",
 16:"AI応答ストリーミング組込み",
 17:"会話履歴とユーザー名管理",
 18:"デプロイ＆疎通",
 19:"UX/エラーハンドリング改善",
 20:"RAG概念/設計（根拠付き回答）",
 21:"Blob格納と分割方針の検討",
 22:"検索→プロンプト結合→回答の実装",
 23:"RAGのWeb UI化（最小）",
 24:"ベクトル検索/評価（計画）",
 25:"実データ適用の検討",
 26:"チャットにRAG統合",
 27:"RAGまとめ",
 28:"Fine-tune準備（JSONL）",
 29:"Fine-tune実行（小規模→本番）",
 30:"効果検証（比較）",
 31:"用途別使い分け",
 32:"最適化（コスト/キャッシュ）",
 33:"ガードレール実装",
 34:"FT/ガードレールまとめ",
 35:"Monitor/ダッシュボード",
 36:"IaCテンプレ化",
 37:"GitHub整理/README強化",
 38:"CI/CD（Zenn/Deploy/Tests）",
 39:"公開戦略（タグ/連携/告知）",
 40:"総括と次の展開"
}

for day in range(2, 41):
    title = titles.get(day, "TBD")
    (CURR / f"day-{day:02d}.md").write_text(template.format(num=day, title=title), encoding="utf-8")

print("Scaffolded: day-02..day-40")
