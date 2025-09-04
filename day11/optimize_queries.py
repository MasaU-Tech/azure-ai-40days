# FILE: C:\dev\azure-ai-40days\day11\optimize_queries.py
# 目的: 同義語展開クエリで Azure AI Search の当たりを比較
# 仕様: 環境変数でパーサ(SIMPLE/FULL)と検索対象(content/all)を切替可能
import os
import re
import csv
from datetime import datetime

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType

# ========= 環境変数 =========
load_dotenv()
endpoint   = os.environ["AZURE_SEARCH_ENDPOINT"].strip().rstrip("/")
index_name = os.getenv("INDEX_NAME", "docs-idx").strip()
key        = (os.getenv("AZURE_SEARCH_ADMIN_KEY") or os.getenv("AZURE_SEARCH_QUERY_KEY") or "").strip()
if not endpoint or not key or not index_name:
    raise SystemExit("環境変数が不足: AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_ADMIN_KEY(or QUERY_KEY) / INDEX_NAME を確認してください。")

# A/B用トグル（PowerShellから切替可）
PARSER = os.getenv("SEARCH_PARSER", "simple").lower()   # simple | full
FIELDS = os.getenv("SEARCH_FIELDS", "content").lower()  # content | all
DEBUG_TOPK = os.getenv("DEBUG_TOPK", "0") in ("1", "true", "True")

QUERY_TYPE = QueryType.FULL if PARSER == "full" else QueryType.SIMPLE

sc = SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))

# ========= 同義語辞書 =========
SYN = {
    "費用": ["コスト", "料金", "価格", "課金", "請求", "従量", "単価", "見積", "見積もり"],
    "手順": ["やり方", "方法", "手続き", "ステップ", "セットアップ", "インストール", "初期化", "使い方", "流れ"],
    "エラー": [
        "不具合","失敗","例外","警告","障害",
        "error","errors","exception","exceptions",
        "traceback","stack trace","stacktrace",
        "fail","failure","bug","crash","warning","message","errmsg"
    ],
}

# 検証クエリ
QUERIES = ["費用", "手順", "エラー"]

# ========= ユーティリティ =========
def expand(q: str) -> str:
    """トグルに応じて展開。FULLのときは語句を適宜クォートして厳密化。"""
    terms = [q] + SYN.get(q, [])
    if PARSER == "full":
        quoted = [f'"{t}"' if (" " in t or t.isalpha()) else t for t in terms]
        return "(" + " OR ".join(quoted) + ")"
    return " OR ".join(terms) if len(terms) > 1 else q

def _as_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)

def _get(d, key, default=None):
    try:
        return d[key]
    except Exception:
        try:
            return getattr(d, key)
        except Exception:
            return default

def _clean_snippet(s: str, max_len: int = 80) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)
    return s if len(s) <= max_len else s[:max_len] + "..."

def _search_kwargs():
    kw = {
        "top": 5,
        "select": ["metadata_storage_name"],
        "query_type": QUERY_TYPE
    }
    if FIELDS == "content":
        kw["search_fields"] = ["content"]
        # 旧SDK互換のため highlight_fields は文字列で渡す
        kw["highlight_fields"] = "content"
        kw["highlight_pre_tag"] = "<em>"
        kw["highlight_post_tag"] = "</em>"
    # FIELDS=all のときは search_fields を敢えて指定しない（＝全searchable）
    return kw

# ========= 検索（Top1 + snippet） =========
def top1(query: str):
    kw = {k: v for k, v in _search_kwargs().items() if v}  # Noneを除去
    try:
        rs = sc.search(search_text=query, **kw)
    except HttpResponseError:
        # 1段目: ハイライト無し
        kw.pop("highlight_fields", None)
        kw.pop("highlight_pre_tag", None)
        kw.pop("highlight_post_tag", None)
        try:
            rs = sc.search(search_text=query, **kw)
        except HttpResponseError:
            # 2段目: search_fields も外して全searchableに
            kw.pop("search_fields", None)
            rs = sc.search(search_text=query, **kw)

    first = next(iter(rs), None)
    if not first:
        return (0.0, "(no hit)", "")

    score = _as_float(_get(first, "@search.score", 0.0))
    name  = _get(first, "metadata_storage_name", "(no name)")

    snippet = ""
    try:
        highlights = _get(first, "@search.highlights", {}) or {}
        cand = highlights.get("content") or []
        if cand:
            snippet = cand[0]
    except Exception:
        pass

    return (score, name, snippet)

def debug_topk(q: str, k=3):
    if not DEBUG_TOPK:
        return []
    rs = sc.search(search_text=q, top=k, select=["metadata_storage_name"])
    return [(float(_get(d, "@search.score", 0.0)), _get(d, "metadata_storage_name", "(no name)")) for d in rs]

# ========= メイン =========
def main():
    print("=== RAG Query Optimization (Base vs Expanded) ===")
    print(f"(parser={PARSER.upper()}, fields={FIELDS})")
    improved = 0
    for q in QUERIES:
        base_q = q
        exp_q  = expand(q)

        s1, n1, sn1 = top1(base_q)
        s2, n2, sn2 = top1(exp_q)

        # 先にスニペット（重複は出さない／整形して短く）
        if sn1:
            print(f"   └ [Base] {_clean_snippet(sn1)}")
        if sn2 and sn2 != sn1:
            print(f"   └ [Expanded] {_clean_snippet(sn2)}")

        flag = "↑" if s2 > s1 else ("=" if s2 == s1 else "↓")
        if s2 > s1:
            improved += 1
        print(f"[{q}] Base: {s1:.3f} {n1}  | Expanded: {s2:.3f} {n2}  -> {flag}")

        # 任意のTopK内訳（DEBUG_TOPK=1 で有効）
        topk_b = debug_topk(base_q)
        topk_e = debug_topk(exp_q)
        if topk_b:
            print("   [Top3/Base]     ", topk_b)
        if topk_e:
            print("   [Top3/Expanded] ", topk_e)

    print(f"\nSummary: improved {improved}/{len(QUERIES)} queries by synonym expansion.")
    print("Tips: SYN 辞書に略語/別表記を追加→再実行で改善率を確認してください。")

    # CSVに記録
    os.makedirs("day11", exist_ok=True)
    with open("day11/query_result.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([datetime.now().isoformat(timespec="seconds"), PARSER, FIELDS, improved, len(QUERIES)])

if __name__ == "__main__":
    main()
