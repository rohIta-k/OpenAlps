"""Contract validator (stdlib only). Exit code 1 if anything violates the official output contract."""
import argparse
import json
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--cases", required=True)
ap.add_argument("--predictions", required=True)
a = ap.parse_args()

NAMES = {0: "entailment", 1: "neutral", 2: "contradiction"}
cases = {}
for line in open(a.cases, encoding="utf-8"):
    if line.strip():
        c = json.loads(line)
        cases[c["id"]] = c

preds, errs = {}, []
for n, line in enumerate(open(a.predictions, encoding="utf-8"), 1):
    if not line.strip():
        continue
    try:
        p = json.loads(line)
        if p["id"] in preds:
            errs.append(f"{p['id']}: duplicate response")
        preds[p["id"]] = p
    except Exception as e:
        errs.append(f"line {n}: invalid JSON ({e})")

for i, c in cases.items():
    p = preds.get(i)
    if p is None:
        errs.append(f"{i}: missing response")
        continue
    lab = p.get("label")
    if isinstance(lab, bool) or lab not in NAMES or p.get("label_name") != NAMES[lab]:
        errs.append(f"{i}: bad label/label_name")
    ev = p.get("evidence")
    if not isinstance(ev, list):
        errs.append(f"{i}: evidence is not a list")
        continue
    if len(ev) > 5:
        errs.append(f"{i}: more than 5 evidence items (only the first 5 are scored)")
    for e in ev:
        if not isinstance(e, dict) or not isinstance(e.get("text"), str) or not e["text"].strip():
            errs.append(f"{i}: evidence item without text")
            continue
        if len(e["text"]) > 5000:
            errs.append(f"{i}: evidence text longer than ~5000 chars (does not count)")
        if "booklet" in c and not (isinstance(e.get("page"), int) and e["page"] >= 1):
            errs.append(f"{i}: task A evidence page must be an int >= 1 (1-based)")
        if "reference" in c and e.get("page") is not None:
            errs.append(f"{i}: task B evidence page must be null")
    if "booklet" in c and lab in (0, 2) and not ev:
        errs.append(f"{i}: task A label 0/2 needs at least one evidence item")
    m = p.get("metrics", {})
    for k in ("input_tokens", "output_tokens", "inference_time_ms"):
        if isinstance(m.get(k), bool) or not isinstance(m.get(k), int) or m[k] < 0:
            errs.append(f"{i}: metrics.{k} must be a non-negative int")

extra = set(preds) - set(cases)
if extra:
    errs.append(f"{len(extra)} responses for unknown ids (e.g. {sorted(extra)[:3]})")
for e in errs[:50]:
    print("ERR", e)
print(f"{len(preds)}/{len(cases)} predictions, {len(errs)} problems")
sys.exit(1 if errs else 0)
