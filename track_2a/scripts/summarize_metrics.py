"""Tokens and latency per task (numbers for the technical report's cost table)."""
import argparse
import json
import statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("--predictions", required=True)
rows = [json.loads(x) for x in open(ap.parse_args().predictions, encoding="utf-8") if x.strip()]
for task in ("A", "B"):
    r = [x for x in rows if x["id"].endswith("-" + task)]
    if not r:
        continue
    ti = [x["metrics"]["input_tokens"] for x in r]
    to = [x["metrics"]["output_tokens"] for x in r]
    ms = sorted(x["metrics"]["inference_time_ms"] for x in r)
    p95 = ms[int(0.95 * (len(ms) - 1))]
    print(f"task {task}: n={len(r)} | in-tok avg={st.mean(ti):.0f} max={max(ti)} total={sum(ti)} | "
          f"out-tok avg={st.mean(to):.0f} total={sum(to)} | ms avg={st.mean(ms):.0f} p95={p95} | "
          f"zero-token(fallback)={sum(1 for t in ti if t == 0)}")
