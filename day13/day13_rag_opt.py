# day13/day13_rag_opt.py
# ---------------------------------------------
# 恒久対応パッチ適用版
# - 親フォルダ(プロジェクト直下)の .env を自動探索・読込
# - 互換名を許容（AZURE_* 系 / 旧 AOAI_* 系どちらでも可）
# - USE_SEMANTIC / MAX_CHARS / TOPK_LIST を環境変数で切替
# - Semantic未対応サービスへの自動フォールバック（semantic→keyword）
# - 429/503 などに対する指数バックオフ＋ジッタのリトライ
# - 失敗時も CSV にエラーを記録して継続（打ち切らない）
# - エンドポイントの https:// / 末尾スラッシュを自動補正
# - Azure AI Search & Azure OpenAI の最小実行＋簡易キャッシュ
# - CSV(results.csv) に計測ログを追記
# ---------------------------------------------

import os
import json
import time
import random
import hashlib
import csv
import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, List

import requests
from dotenv import load_dotenv, find_dotenv

# ========= ユーティリティ =========
def _normalize_endpoint(u: str | None) -> str:
    if not u:
        return ""
    u = u.strip()
    if u.endswith("/"):
        u = u[:-1]
    if not (u.startswith("http://") or u.startswith("https://")):
        u = "https://" + u
    return u

def _require_env(name: str, value: str | None):
    if not value:
        raise RuntimeError(
            f"[CONFIG ERROR] .env の '{name}' が未設定です。"
            f" C:\\dev\\azure-ai-40days\\.env に {name}=... を追加してください。"
        )
    return value

def _truthy(s: Any) -> bool:
    return str(s).lower() in ("1", "true", "yes", "on")

def _post_retry(url: str, headers: Dict[str, str], payload: Dict[str, Any],
                timeout: float, max_retry: int = 5) -> requests.Response:
    """
    429/503 に指数バックオフ＋ジッタでリトライ。その他のHTTPは即raise。
    """
    wait = 1.0
    for _ in range(max_retry):
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if r.status_code in (429, 503):
            ra = r.headers.get("retry-after")
            sleep = float(ra) if ra else wait + random.random()
            time.sleep(min(sleep, 30))
            wait = min(wait * 2, 16)
            continue
        r.raise_for_status()
        return r
    # 最後の試行も失敗した場合は詳細付で例外
    try:
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"max retry exceeded for {url}: {getattr(e, 'response', None) and getattr(e.response, 'text', '')}") from e
    raise RuntimeError("max retry exceeded")

# ========= .env ロード（ローカル→親探索→ルート直指定） =========
loaded = load_dotenv(Path(__file__).with_name(".env"))
if not loaded:
    env_path = find_dotenv(filename=".env", usecwd=True)
    if env_path:
        load_dotenv(env_path)
    else:
        root_env = Path(__file__).resolve().parent.parent / ".env"
        if root_env.exists():
            load_dotenv(root_env)

# ========= 必須変数の取得・検証（互換名対応） =========
# Azure OpenAI
AOAI_EP = _normalize_endpoint(
    os.getenv("AOAI_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
)
AOAI_KEY = (
    os.getenv("AOAI_KEY")
    or os.getenv("AZURE_OPENAI_API_KEY")
    or os.getenv("AZURE_OPENAI_KEY")
)
DEPLOY = os.getenv("AOAI_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT")
AOAI_API_VERSION = (
    os.getenv("AOAI_API_VERSION")
    or os.getenv("AZURE_OPENAI_API_VERSION")
    or "2024-07-18"
)

# Azure AI Search
SEARCH_EP = _normalize_endpoint(
    os.getenv("AZ_SEARCH_ENDPOINT") or os.getenv("AZURE_SEARCH_ENDPOINT")
)
SEARCH_KEY = (
    os.getenv("AZ_SEARCH_KEY")
    or os.getenv("AZURE_SEARCH_ADMIN_KEY")
    or os.getenv("AZURE_SEARCH_QUERY_KEY")
)
INDEX = os.getenv("AZ_SEARCH_INDEX") or os.getenv("INDEX_NAME")

# 価格（任意：円/1Ktoken）
IN_PRICE = float(os.getenv("INPUT_PRICE_PER1K", "0") or "0")
OUT_PRICE = float(os.getenv("OUTPUT_PRICE_PER1K", "0") or "0")

# チューニング切替（環境変数）
USE_SEMANTIC = _truthy(os.getenv("USE_SEMANTIC", "0"))
try:
    MAX_CHARS = int(os.getenv("MAX_CHARS", "0") or "0")  # 0なら圧縮しない
except ValueError:
    MAX_CHARS = 0

# topK の実験セット（例: "1,3,5" / "3"）
_topk_env = os.getenv("TOPK_LIST") or os.getenv("TOPK")
if _topk_env:
    TOPK_LIST: List[int] = []
    for p in _topk_env.split(","):
        p = p.strip()
        if not p:
            continue
        try:
            TOPK_LIST.append(int(p))
        except ValueError:
            pass
    if not TOPK_LIST:
        TOPK_LIST = [1, 3, 5]
else:
    TOPK_LIST = [1, 3, 5]

# 必須チェック
_require_env("AOAI_ENDPOINT", AOAI_EP)
_require_env("AOAI_KEY", AOAI_KEY)
_require_env("AOAI_DEPLOYMENT", DEPLOY)
_require_env("AZ_SEARCH_ENDPOINT", SEARCH_EP)
_require_env("AZ_SEARCH_KEY", SEARCH_KEY)
_require_env("AZ_SEARCH_INDEX", INDEX)

# ========= キャッシュ =========
CACHE_DIR = Path(__file__).with_name("cache")
CACHE_DIR.mkdir(exist_ok=True)
SCACHE = CACHE_DIR / "search_cache.json"
LCACHE = CACHE_DIR / "llm_cache.json"

def _load_json(p: Path) -> Dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_json(p: Path, data: Dict[str, Any]) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ========= Azure AI Search =========
def _extract_doc_text(doc: Dict[str, Any]) -> str:
    """
    インデックスの本文フィールド名が環境により異なる想定に対応。
    優先順で探し、見つからなければ doc 全体をJSON化して返す。
    """
    candidates = ["content", "text", "chunk", "pageContent", "body"]
    for k in candidates:
        if k in doc and isinstance(doc[k], str):
            return doc[k]
    if "_source" in doc and isinstance(doc["_source"], dict):
        for k in candidates:
            v = doc["_source"].get(k)
            if isinstance(v, str):
                return v
    return json.dumps(doc, ensure_ascii=False)

def search(query: str, top_k: int = 3) -> Tuple[List[str], bool]:
    cache_key = f"{INDEX}|{query}|k={top_k}|semantic={int(USE_SEMANTIC)}"
    cache = _load_json(SCACHE)
    if cache_key in cache:
        return cache[cache_key], True

    base = SEARCH_EP.rstrip("/")
    url = f"{base}/indexes/{INDEX}/docs/search?api-version=2023-11-01"
    payload: Dict[str, Any] = {"search": query, "top": top_k}
    if USE_SEMANTIC:
        payload.update({
            "queryType": "semantic",
            "semanticConfiguration": "default"
        })

    headers = {"api-key": SEARCH_KEY, "Content-Type": "application/json"}

    # まずは（必要なら）semanticで試行 → Semantic未対応ならキーワードに自動フォールバック
    try:
        r = _post_retry(url, headers, payload, timeout=20)
    except requests.exceptions.HTTPError as e:
        txt = ""
        try:
            txt = e.response.text  # type: ignore
        except Exception:
            pass
        if ("Semantic search is not enabled" in txt) or ("SemanticQueriesNotAvailable" in txt):
            # フォールバック：semanticパラメータを外して再送
            payload.pop("queryType", None)
            payload.pop("semanticConfiguration", None)
            r = _post_retry(url, headers, payload, timeout=20)
        else:
            raise
    except Exception:
        # _post_retry からのRuntimeErrorなどもそのまま上位へ
        raise

    j = r.json()
    items = j.get("value", [])
    docs = [_extract_doc_text(item) for item in items]
    cache[cache_key] = docs
    _save_json(SCACHE, cache)
    return docs, False

# ========= Azure OpenAI (Chat Completions) =========
def chat(query: str, context: str) -> Tuple[Dict[str, Any], bool]:
    key_src = f"{DEPLOY}\n{query}\n{hashlib.sha256(context.encode('utf-8')).hexdigest()}"
    cache_key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()
    cache = _load_json(LCACHE)
    if cache_key in cache:
        return cache[cache_key], True

    url = f"{AOAI_EP}/openai/deployments/{DEPLOY}/chat/completions?api-version={AOAI_API_VERSION}"
    body = {
        "messages": [
            {"role": "system", "content": "Use ONLY the provided context. If context is missing, say so briefly."},
            {"role": "user", "content": f"# Query\n{query}\n\n# Context\n{context}"},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }
    headers = {"api-key": AOAI_KEY, "Content-Type": "application/json"}

    r = _post_retry(url, headers, body, timeout=60)
    data = r.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    result = {"content": content, "usage": usage}
    cache[cache_key] = result
    _save_json(LCACHE, cache)
    return result, False

# ========= 実行ルーチン =========
CSV_FIELDS = [
    "ts", "query", "topK", "use_semantic", "max_chars",
    "search_cache", "llm_cache",
    "search_sec", "llm_sec",
    "in_tokens", "out_tokens", "est_jpy",
    "error",
]

def _estimate_jpy(usage: Dict[str, Any]) -> float | None:
    if not (IN_PRICE or OUT_PRICE):
        return None
    in_t = usage.get("prompt_tokens", 0) or usage.get("total_tokens", 0)
    out_t = usage.get("completion_tokens", 0)
    return (in_t / 1000.0) * IN_PRICE + (out_t / 1000.0) * OUT_PRICE

def _append_csv(row: Dict[str, Any]) -> None:
    logf = Path(__file__).with_name("results.csv")
    new = not logf.exists()
    with logf.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        # 欠損キーを空で埋める
        for k in CSV_FIELDS:
            row.setdefault(k, "")
        w.writerow(row)

def run(query: str = "RAGの最適化ポイントを要約して") -> None:
    for top_k in TOPK_LIST:
        try:
            # Search
            t0 = time.time()
            docs, hit_s = search(query, top_k)
            t1 = time.time()

            # 結果順の揺れ対策（キャッシュキー安定に寄与・任意）
            docs = sorted(docs)

            # 文脈圧縮（MAX_CHARS > 0 の場合）
            if MAX_CHARS > 0:
                ctx = "\n\n".join(d[:MAX_CHARS] for d in docs) if docs else "（検索結果なし）"
            else:
                ctx = "\n\n".join(docs) if docs else "（検索結果なし）"

            # LLM
            res, hit_l = chat(query, ctx)
            t2 = time.time()

            usage = res.get("usage", {})
            in_t = usage.get("prompt_tokens", 0)
            out_t = usage.get("completion_tokens", 0)
            jpy = _estimate_jpy(usage)

            print(f"[topK={top_k}] search: {'cache' if hit_s else 'live'} {t1 - t0:.2f}s, "
                  f"llm: {'cache' if hit_l else 'live'} {t2 - t1:.2f}s")
            meta = f"tokens in/out={in_t}/{out_t}"
            if jpy is not None:
                meta += f", est ¥{jpy:.2f}"
            print(" ", meta)
            ans = (res.get("content") or "").strip().replace("\n", " ")
            print("  answer:", (ans[:180] + (" ..." if len(ans) > 180 else "")))
            print()

            _append_csv({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "query": query,
                "topK": top_k,
                "use_semantic": "1" if USE_SEMANTIC else "0",
                "max_chars": MAX_CHARS,
                "search_cache": hit_s,
                "llm_cache": hit_l,
                "search_sec": round(t1 - t0, 3),
                "llm_sec": round(t2 - t1, 3),
                "in_tokens": int(in_t or 0),
                "out_tokens": int(out_t or 0),
                "est_jpy": round(jpy or 0, 6),
                "error": "",
            })

        except Exception as e:
            # 失敗しても継続し、CSVに記録
            msg = str(e)
            print(f"[WARN] topK={top_k} skipped due to error: {msg}")
            _append_csv({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "query": query,
                "topK": top_k,
                "use_semantic": "1" if USE_SEMANTIC else "0",
                "max_chars": MAX_CHARS,
                "search_cache": "",
                "llm_cache": "",
                "search_sec": "",
                "llm_sec": "",
                "in_tokens": "",
                "out_tokens": "",
                "est_jpy": "",
                "error": msg[:500],
            })
            continue

        # answers.jsonl に回答本文も保存（Day14の自動採点で使える）
        anslog = Path(__file__).with_name("answers.jsonl")
        with anslog.open("a", encoding="utf-8") as f:
            import json
            f.write(json.dumps({
                "ts": row["ts"], "query": query, "topK": top_k,
                "use_semantic": row["use_semantic"], "max_chars": row["max_chars"],
                "answer": (res.get("content") or "")
            }, ensure_ascii=False) + "\n")

# ========= エントリーポイント =========
if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    run(q or "RAGの最適化ポイントを要約して")
