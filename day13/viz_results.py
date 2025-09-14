# day13/viz_results.py
# ---------------------------------------------------
# results.csv を集計して PNG グラフを images/day13/ に出力
# - グラフ1: topK別 平均LLM遅延（秒）
# - グラフ2: 圧縮(有/無)別 平均入力トークン数
# - グラフ3: セマンティック(ON/OFF)別 平均推定コスト(円)
# 使い方:  python viz_results.py  [CSVパス省略可]
# ---------------------------------------------------

import sys
import csv
import statistics
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt


def load_rows(csv_path: Path) -> List[Dict[str, Any]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def to_bool(v: Any) -> bool:
    return str(v).lower() in ("1", "true", "yes", "on")


def to_int(v: Any, default: int = 0) -> int:
    try:
        return int(str(v).strip())
    except Exception:
        return default


def to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(str(v).strip())
    except Exception:
        return default


def coerce_types(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        rr = dict(r)
        rr["topK"] = to_int(rr.get("topK", 0), 0)
        rr["search_sec"] = to_float(rr.get("search_sec", 0.0), 0.0)
        rr["llm_sec"] = to_float(rr.get("llm_sec", 0.0), 0.0)
        rr["in_tokens"] = to_int(rr.get("in_tokens", 0), 0)
        rr["out_tokens"] = to_int(rr.get("out_tokens", 0), 0)
        rr["est_jpy"] = to_float(rr.get("est_jpy", 0.0), 0.0)
        rr["use_semantic"] = to_bool(rr.get("use_semantic", "0"))
        rr["max_chars"] = to_int(rr.get("max_chars", 0), 0)
        rr["error"] = (rr.get("error") or "").strip()
        out.append(rr)
    return out


def ensure_outdir(root: Path) -> Path:
    outdir = root / "images" / "day13"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def agg_mean(rows: List[Dict[str, Any]], key_fn, metric: str) -> Dict[Any, float]:
    buckets: Dict[Any, List[float]] = {}
    for r in rows:
        # 数値が有効な行のみ
        val = r.get(metric, None)
        if isinstance(val, (int, float)):
            k = key_fn(r)
            buckets.setdefault(k, []).append(float(val))
    return {k: statistics.mean(v) for k, v in buckets.items() if v}


def plot_bar(x_labels: List[str], y_values: List[float], title: str, xlabel: str, ylabel: str, path: Path):
    plt.figure()
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.bar(x_labels, y_values)  # 色指定なし（要件）
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    # スクリプトの隣にある results.csv を既定とする
    here = Path(__file__).resolve().parent
    csv_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (here / "results.csv")
    outdir = ensure_outdir(here)

    rows_raw = load_rows(csv_path)
    rows = coerce_types(rows_raw)

    # 集計対象は基本的に error が空の成功行のみ（失敗行は除外）
    ok_rows = [r for r in rows if not r["error"]]

    if not ok_rows:
        print("No valid rows to visualize (all rows had errors).")
        return

    # 1) topK別 平均LLM遅延（秒）
    topk_llm = agg_mean(ok_rows, key_fn=lambda r: r["topK"], metric="llm_sec")
    if topk_llm:
        xs = sorted(topk_llm.keys())
        ys = [topk_llm[x] for x in xs]
        plot_bar([str(x) for x in xs], ys,
                 title="LLM latency by topK (avg)",
                 xlabel="topK", ylabel="seconds",
                 path=outdir / "llm_latency_by_topk.png")
    else:
        print("WARN: no data for LLM latency by topK")

    # 2) 圧縮有無での平均入力トークン
    cmp_in = agg_mean(ok_rows,
                      key_fn=lambda r: "compressed" if r["max_chars"] > 0 else "no-compress",
                      metric="in_tokens")
    if cmp_in:
        xs2 = list(cmp_in.keys())
        ys2 = [cmp_in[x] for x in xs2]
        plot_bar(xs2, ys2,
                 title="Prompt tokens (avg): compression vs no-compression",
                 xlabel="mode", ylabel="tokens",
                 path=outdir / "tokens_compress.png")
    else:
        print("WARN: no data for tokens (compression)")

    # 3) セマンティック有無での平均推定コスト(円)
    sem_cost = agg_mean(ok_rows,
                        key_fn=lambda r: "semantic-on" if r["use_semantic"] else "semantic-off",
                        metric="est_jpy")
    if sem_cost:
        xs3 = list(sem_cost.keys())
        ys3 = [sem_cost[x] for x in xs3]
        plot_bar(xs3, ys3,
                 title="Estimated cost (avg): semantic on/off",
                 xlabel="mode", ylabel="JPY",
                 path=outdir / "cost_semantic.png")
    else:
        print("WARN: no data for estimated cost (semantic on/off)")

    # --- コンソールに概要出力 ---
    def p_map(title: str, m: Dict[Any, float], unit: str = ""):
        print(f"\n== {title} ==")
        for k in sorted(m, key=lambda x: str(x)):
            print(f"{k} -> {round(m[k], 4)}{unit}")

    if topk_llm:
        p_map("Avg LLM latency by topK", topk_llm, " sec")
    if cmp_in:
        p_map("Avg prompt tokens: compression vs no-compression", cmp_in)
    if sem_cost:
        p_map("Avg estimated cost: semantic on/off", sem_cost, " JPY")

    # 参考：基本統計量
    try:
        all_llm = [r["llm_sec"] for r in ok_rows if r["llm_sec"] > 0]
        if all_llm:
            print(f"\nLLM latency: count={len(all_llm)}, mean={statistics.mean(all_llm):.4f}, "
                  f"p50≈{statistics.median(all_llm):.4f}, min={min(all_llm):.4f}, max={max(all_llm):.4f}")
    except Exception:
        pass

    print(f"\nSaved charts under: {outdir}")


if __name__ == "__main__":
    main()
