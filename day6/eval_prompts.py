# eval_prompts.py  — Day6 改善版（キーワード必須・BOM対策・.env読込）
# 使い方:
#   py -m pip install openai==1.* python-dotenv pandas matplotlib
#   python .\eval_prompts.py

import os
import json
import csv
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AzureOpenAI


# ---------- .env 読み込み ----------
# ルート直下（..）→カレント（.）の順で探索
project_root_env = Path(__file__).resolve().parents[1] / ".env"
loaded = load_dotenv(dotenv_path=project_root_env) or load_dotenv()
# 読み込めていなくても続行（環境変数で渡されるケースを考慮）

ENDPOINT   = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY    = os.getenv("AZURE_OPENAI_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # 例: gpt4o-mini-chat
API_VER    = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-07-18"

# 軽いバリデーション（足りない場合でも例外は投げず警告のみ）
def warn_env(name, val):
    if not val:
        print(f"[WARN] {name} が未設定です。 .env もしくは環境変数を確認してください。")

warn_env("AZURE_OPENAI_ENDPOINT", ENDPOINT)
warn_env("AZURE_OPENAI_KEY", API_KEY)
warn_env("AZURE_OPENAI_DEPLOYMENT", DEPLOYMENT)

# ---------- Azure OpenAI Client ----------
client = AzureOpenAI(
    api_key=API_KEY,
    api_version=API_VER,
    azure_endpoint=ENDPOINT
)

# ---------- プロンプト定義 ----------
BASE_SYS = "あなたは端的に答えるアシスタントです。"
BASE_USER_TMPL = "質問: {q}\n要点だけ短く答えて。"

# 改善版: “必ず含める語”を明示して短文でもキーワードが落ちないようにする
IMPROVED_SYS = (
    "あなたはAzure AI学習者向けの日本語アシスタントです。"
    "回答は1〜2文で簡潔に、自然な日本語で。"
    "質問に固有の重要語を省略せず、指定されたキーワードを最低1回はそのまま含めてください。"
    "不要な前置きや婉曲表現は禁止。"
)
IMPROVED_USER_TMPL = (
    "次の質問に1〜2文で答えてください。"
    "必ず次のキーワードを最低1回以上含めること: {keywords}\n"
    "質問: {q}"
)

# ---------- 呼び出し関数 ----------
def ask(model_deploy: str, sys_msg: str, user_msg: str) -> str:
    resp = client.chat.completions.create(
        model=model_deploy,
        messages=[
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.1,   # 指示遵守を高める
        max_tokens=256,    # 出力短縮でコスト抑制
    )
    return (resp.choices[0].message.content or "").strip()

# ---------- スコア関数（超簡易: キーワード完全一致率） ----------
def score_answer(ans: str, keywords_csv: str) -> float:
    ans = ans or ""
    keys = [k.strip() for k in (keywords_csv or "").split(",") if k.strip()]
    if not keys:
        return 0.0
    hits = sum(1 for k in keys if k in ans)
    return hits / len(keys)

# ---------- 入出力パス ----------
CWD = Path(__file__).resolve().parent
TESTSET = CWD / "testset.jsonl"
IMG_DIR = CWD.parents[1] /"articles"/ "images" / "day6"  # ../images/day6
IMG_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = CWD / "results_day6.csv"
OUT_PNG = IMG_DIR / "prompt_compare.png"

# ---------- メイン処理 ----------
def main():
    if not TESTSET.exists():
        raise FileNotFoundError(f"testset.jsonl が見つかりません: {TESTSET}")

    rows = []
    # PowerShell Out-File の BOM 付きに対応（utf-8-sig）
    with open(TESTSET, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            q = item.get("question", "").strip()
            kw = item.get("keywords", "").strip()  # 例: "Azure,OpenAI"

            # base
            base_ans = ask(DEPLOYMENT, BASE_SYS, BASE_USER_TMPL.format(q=q))

            # improved（キーワードを明示的に渡す。空なら“指定なし”とする）
            kw_for_prompt = kw if kw else "（指定なし）"
            impv_ans = ask(
                DEPLOYMENT,
                IMPROVED_SYS,
                IMPROVED_USER_TMPL.format(q=q, keywords=kw_for_prompt)
            )

            base_sc = score_answer(base_ans, kw)
            impv_sc = score_answer(impv_ans, kw)

            rows.append({
                "id": item.get("id"),
                "question": q,
                "keywords": kw,
                "base_answer": base_ans,
                "improved_answer": impv_ans,
                "base_score": base_sc,
                "improved_score": impv_sc,
            })

    if not rows:
        print("[WARN] testset.jsonl に有効なデータがありません。")
        return

    # CSV保存
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # 集計＆可視化
    df = pd.DataFrame(rows)
    avg_base = float(df["base_score"].mean())
    avg_impr = float(df["improved_score"].mean())

    print(f"Base Avg: {avg_base:.3f}")
    print(f"Improved Avg: {avg_impr:.3f}")

    # 棒グラフ（seabornは使わず、単一プロット）
    plt.figure()
    df[["base_score", "improved_score"]].mean().plot(
        kind="bar", title="Prompt Score Comparison"
    )
    plt.ylabel("Average keyword hit ratio")
    plt.tight_layout()
    plt.savefig(OUT_PNG)

    print(f"Saved: {OUT_CSV.name}, {OUT_PNG}")

if __name__ == "__main__":
    main()
