"""Fast local scoring: macro-F1 per task and per claim->source language pair, with confusion matrices."""
import argparse
import collections
import json

from sklearn.metrics import classification_report, confusion_matrix, f1_score

ap = argparse.ArgumentParser()
ap.add_argument("--predictions", required=True)
ap.add_argument("--expected", required=True)
ap.add_argument("--cases", required=True)
a = ap.parse_args()

def rd(p):
    return {j["id"]: j for j in (json.loads(x) for x in open(p, encoding="utf-8") if x.strip())}

pred, gold, cases = rd(a.predictions), rd(a.expected), rd(a.cases)

def report(ids, title, full=False):
    ids = [i for i in ids if i in gold and i in pred]
    if not ids:
        return
    y = [gold[i]["label"] for i in ids]
    p = [pred[i]["label"] for i in ids]
    f1 = f1_score(y, p, average="macro", labels=[0, 1, 2], zero_division=0)
    acc = sum(u == v for u, v in zip(y, p)) / len(y)
    print(f"{title}: n={len(ids)} macro-F1={f1:.3f} acc={acc:.3f}")
    if full:
        print(classification_report(y, p, labels=[0, 1, 2], target_names=["ent", "neu", "con"], digits=3, zero_division=0))
        print(confusion_matrix(y, p, labels=[0, 1, 2]), "\n")

for task in ("A", "B"):
    ids = [i for i in cases if i.endswith("-" + task)]
    report(ids, f"== task {task}", full=True)
    pairs = collections.defaultdict(list)
    for i in ids:
        c = cases[i]
        src = (c.get("booklet") or c.get("reference"))["language"]
        pairs[f"{c['claim']['language']}->{src}"].append(i)
    for k, v in sorted(pairs.items()):
        report(v, f"   {task} {k}")
