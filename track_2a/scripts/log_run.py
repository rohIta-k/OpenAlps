"""Append one row to docs/experiments.csv (score + cost monitoring) and print cumulative token spend.
Example:
  python scripts/log_run.py --name P2-A-full-8B --predictions output/pred_a.jsonl \
      --expected data/dev/expected-labels.jsonl --cases data/dev/cases.jsonl --model Apertus-v1.5-8B --notes "baseline"
"""
import argparse
import csv
import datetime
import json
import os
import statistics as st

from sklearn.metrics import f1_score

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--predictions", required=True)
ap.add_argument("--expected", required=True)
ap.add_argument("--cases", required=True)
ap.add_argument("--model", default="")
ap.add_argument("--notes", default="")
ap.add_argument("--csv", default="docs/experiments.csv")
a = ap.parse_args()


def rd(p):
    return {j["id"]: j for j in (json.loads(x) for x in open(p, encoding="utf-8") if x.strip())}


pred, gold, cases = rd(a.predictions), rd(a.expected), rd(a.cases)
FIELDS = ["date", "name", "task", "model", "n", "macro_f1", "acc", "in_tok_avg", "in_tok_total",
          "out_tok_total", "ms_avg", "ms_p95", "fallbacks", "ev_missing_02", "ev_pagetext", "notes"]
rows = []
for task in ("A", "B"):
    ids = [i for i in cases if i.endswith("-" + task) and i in pred and i in gold]
    if not ids:
        continue
    y = [gold[i]["label"] for i in ids]
    p = [pred[i]["label"] for i in ids]
    m = [pred[i]["metrics"] for i in ids]
    ms = sorted(x["inference_time_ms"] for x in m)
    ev_missing = sum(1 for i in ids if task == "A" and pred[i]["label"] in (0, 2) and not pred[i]["evidence"])
    # evidence items > 1500 chars are almost always the whole-page fallback (the model did not quote verbatim)
    ev_pagetext = sum(1 for i in ids if task == "A" and any(len(e["text"]) > 1500 for e in pred[i]["evidence"]))
    rows.append({
        "date": datetime.datetime.now().isoformat(timespec="minutes"), "name": a.name, "task": task,
        "model": a.model, "n": len(ids),
        "macro_f1": round(f1_score(y, p, average="macro", labels=[0, 1, 2], zero_division=0), 4),
        "acc": round(sum(u == v for u, v in zip(y, p)) / len(y), 4),
        "in_tok_avg": round(st.mean(x["input_tokens"] for x in m)), "in_tok_total": sum(x["input_tokens"] for x in m),
        "out_tok_total": sum(x["output_tokens"] for x in m), "ms_avg": round(st.mean(ms)),
        "ms_p95": ms[int(0.95 * (len(ms) - 1))], "fallbacks": sum(1 for x in m if x["input_tokens"] == 0),
        "ev_missing_02": ev_missing, "ev_pagetext": ev_pagetext, "notes": a.notes})

os.makedirs(os.path.dirname(a.csv) or ".", exist_ok=True)
new = not os.path.exists(a.csv)
with open(a.csv, "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, FIELDS)
    if new:
        w.writeheader()
    w.writerows(rows)
for r in rows:
    print({k: r[k] for k in ("name", "task", "n", "macro_f1", "in_tok_avg", "ms_avg", "fallbacks", "ev_missing_02", "ev_pagetext")})
tot = sum(int(r["in_tok_total"]) + int(r["out_tok_total"]) for r in csv.DictReader(open(a.csv, encoding="utf-8")))
print(f"CUMULATIVE tokens logged in {a.csv}: {tot:,}  (compare with your quota; keep a reserve for grading)")
