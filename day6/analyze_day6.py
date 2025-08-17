import pandas as pd
import re

# 1) 読み込み
df = pd.read_csv("results_day6.csv")

# 2) 簡易メトリクス: 文章長、キーワード完全一致、Jaccard(期待文との語彙重なり)
def tok(s):  # ゆるいトークナイザ
    return [w for w in re.findall(r"\w+|[一-龠ぁ-んァ-ン]+", str(s))]

def jaccard(a, b):
    A, B = set(tok(a)), set(tok(b))
    return len(A & B) / max(1, len(A | B))

def contains_all(ans, kw_csv):
    kws = [k.strip() for k in str(kw_csv).split(",") if k.strip()]
    return all(k in str(ans) for k in kws)

rows = []
for _, r in df.iterrows():
    exp = r.get("keywords", "")
    base = r.get("base_answer", "")
    impv = r.get("improved_answer", "")
    # 文章長
    base_len = len(base)
    impv_len = len(impv)
    # キーワード完全一致
    base_all = contains_all(base, exp)
    impv_all = contains_all(impv, exp)
    # 期待文（expected）との重なり度
    jac_base = jaccard(r.get("expected",""), base)
    jac_impv = jaccard(r.get("expected",""), impv)
    rows.append((base_len, impv_len, base_all, impv_all, jac_base, jac_impv))

out = pd.DataFrame(rows, columns=["base_len","impv_len","base_allKW","impv_allKW","jac_base","jac_impv"])
print("=== Averages ===")
print(out.mean(numeric_only=True))
print("\n=== Suspicious (keyword stuffing?) ===")
# 極端に短いのに全キーワード一致 → 羅列の疑い
sus = out[(out.impv_len <= 25) & (out.impv_allKW)]
print(sus if len(sus) else "none")
