# to_csv_merge.py — outputs.jsonl (answer, line_number) と questions.csv を結合して CSV を出力
import csv, json

qs = []
with open("questions.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        qs.append(row.get("question"))

with open(r".\outputs\outputs.jsonl", "r", encoding="utf-8") as fin, \
     open(r".\outputs\answers.csv", "w", encoding="utf-8", newline="") as fout:
    w = csv.DictWriter(fout, fieldnames=["question", "answer"])
    w.writeheader()
    for line in fin:
        if not line.strip():
            continue
        o = json.loads(line)
        ln = o.get("line_number")
        ans = o.get("answer")
        q = qs[ln] if isinstance(ln, int) and 0 <= ln < len(qs) else None
        w.writerow({"question": q, "answer": ans})

print("wrote: outputs\\answers.csv")
