"""Is run B really better than run A? Paired bootstrap on macro-F1 (same case ids).
  python scripts/compare_runs.py --a output/pred_b_base.jsonl --b output/pred_b_v2.jsonl \
      --expected data/dev_b/expected-labels.jsonl
Rule of thumb: adopt B only if the 95% interval of (B - A) is above 0, or if it is ~0 and B is clearly cheaper.
"""
import argparse
import json

import numpy as np
from sklearn.metrics import f1_score

ap = argparse.ArgumentParser()
ap.add_argument("--a", required=True)
ap.add_argument("--b", required=True)
ap.add_argument("--expected", required=True)
ap.add_argument("--n", type=int, default=2000, help="bootstrap resamples")
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()


def rd(p):
    return {j["id"]: j for j in (json.loads(x) for x in open(p, encoding="utf-8") if x.strip())}


pa, pb, gold = rd(a.a), rd(a.b), rd(a.expected)
ids = sorted(set(pa) & set(pb) & set(gold))
if not ids:
    raise SystemExit("no common ids")
y = np.array([gold[i]["label"] for i in ids])
ya, yb = np.array([pa[i]["label"] for i in ids]), np.array([pb[i]["label"] for i in ids])


def f1(t, p):
    return f1_score(t, p, average="macro", labels=[0, 1, 2], zero_division=0)


rng = np.random.default_rng(a.seed)
fa, fb, diff = [], [], []
for _ in range(a.n):
    ix = rng.integers(0, len(ids), len(ids))
    x, z = f1(y[ix], ya[ix]), f1(y[ix], yb[ix])
    fa.append(x), fb.append(z), diff.append(z - x)
def ci(v):
    return tuple(round(float(x), 3) for x in np.percentile(v, [2.5, 97.5]))
print(f"n={len(ids)} common cases")
print(f"A macro-F1 {f1(y, ya):.3f}  95% CI {ci(fa)}")
print(f"B macro-F1 {f1(y, yb):.3f}  95% CI {ci(fb)}")
lo, hi = ci(diff)
verdict = "B better" if lo > 0 else "B worse" if hi < 0 else "NO clear difference (noise)"
print(f"B - A      {f1(y, yb) - f1(y, ya):+.3f}  95% CI ({lo}, {hi})  -> {verdict}")
