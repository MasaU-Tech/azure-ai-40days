# day5/viz_scores.py（修正版）
# 目的:
# - Day4の rows.csv / summary.csv を読み込み
# - ヒストグラム & 質問別平均スコアを ../images/day5/ に保存
# - 閾値と合格率を day5/threshold.json に保存
# 方針: matplotlibのみ・単一プロット・色指定なし／フォルダは自動生成

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ===== パス定義（どこで実行しても同じになるように __file__ 基準） =====
THIS = Path(__file__).resolve()          # .../day5/viz_scores.py
ROOT = THIS.parent.parent                # .../azure-ai-40days
DAY4_OUT = ROOT / "day4" / "outputs"     # 入力元（Day4成果物）
IMG_DIR = ROOT / "images" / "day5"       # 出力先（ブログ用に一元管理）
CFG_DIR = ROOT / "day5"                  # 閾値JSONの保存先

rows_path = DAY4_OUT / "rows.csv"
summary_path = DAY4_OUT / "summary.csv"  # 使わないが存在チェック用に読むことも可能
hist_path = IMG_DIR / "score_hist.png"
byq_path = IMG_DIR / "score_by_question.png"
th_config_path = CFG_DIR / "threshold.json"

# 必要フォルダ作成
IMG_DIR.mkdir(parents=True, exist_ok=True)
CFG_DIR.mkdir(parents=True, exist_ok=True)

# ===== 1) 読み込み =====
# encoding は必要に応じて "utf-8-sig" に変更
rows = pd.read_csv(rows_path)
# summary は今は未使用。必要なら読み込み:
# summary = pd.read_csv(summary_path, header=None, names=["key", "value"])

# ===== 2) スコア列を数値化 =====
rows["score"] = pd.to_numeric(rows.get("score", 0), errors="coerce").fillna(0.0)

# ===== 3) ヒストグラム（単一プロット・色指定なし） =====
plt.figure()
rows["score"].hist(bins=10)
plt.title("Score Distribution (Day5)")
plt.xlabel("score")
plt.ylabel("count")
plt.tight_layout()
plt.savefig(hist_path)
plt.close()

# ===== 4) 質問別の平均スコア（棒グラフ：インデックスで描画） =====
by_q = rows[["question", "score"]].copy()
by_q = by_q.groupby("question", as_index=False)["score"].mean()

plt.figure()
plt.bar(range(len(by_q)), by_q["score"])
plt.title("Average Score by Question")
plt.xlabel("question index")
plt.ylabel("avg score")
plt.tight_layout()
plt.savefig(byq_path)
plt.close()

# ===== 5) 暫定閾値の決定 =====
# ルール: 分布の谷が 0.5〜0.9 にあれば採用。無ければ 0.7。
counts, bins = np.histogram(rows["score"], bins=10)
min_bin_idx = int(np.argmin(counts))
candidate = float((bins[min_bin_idx] + bins[min_bin_idx + 1]) / 2.0)
threshold = candidate if 0.5 <= candidate <= 0.9 else 0.7

# ===== 6) 閾値で合否を計算 =====
rows["pass"] = (rows["score"] >= threshold).astype(int)
pass_rate = float(rows["pass"].mean())

# ===== 7) 閾値をJSON保存 =====
with th_config_path.open("w", encoding="utf-8") as f:
    json.dump({"threshold": threshold, "pass_rate": round(pass_rate, 3)}, f, ensure_ascii=False, indent=2)

print(f"[OK] score_hist        : {hist_path}")
print(f"[OK] score_by_question : {byq_path}")
print(f"[OK] threshold         : {threshold:.3f}, pass_rate: {pass_rate:.3f}")
print(f"[OK] config            : {th_config_path}")