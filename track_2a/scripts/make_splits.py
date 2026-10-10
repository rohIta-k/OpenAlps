"""Frozen, leakage-safe splits from the FULL data (run once; free: no model calls, no tokens).

Input : data/full/{cases.jsonl, expected-labels.jsonl, booklets/}   (prepare_cases.py WITHOUT --limit)
Output: data/{dev_a,dev_b,val_a,val_b,test_a,test_b}/{cases.jsonl, expected-labels.jsonl, booklets -> ../full/booklets}
        docs/splits.json   (ids per split; commit it so teammates and CI use identical splits)

Leakage control: the unit of splitting is the VOTING DAY (all proposals of a day and all three language
versions stay in ONE pool). Inside a pool rows are ordered round-robin over (label x language pair), so every
prefix is stratified; dev_a is a prefix of dev_b's rows, so you can compare A and B on the same claims.
test_* = the whole test pool: touch it ONCE, for the final numbers.
"""
import argparse
import json
import os
import random
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="data/full")
ap.add_argument("--out-root", default="data")
ap.add_argument("--splits-json", default="docs/splits.json")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--pools", default="0.5,0.25,0.25", help="share of voting days for dev,val,test")
ap.add_argument("--dev-a", type=int, default=40)
ap.add_argument("--dev-b", type=int, default=100)
ap.add_argument("--val-a", type=int, default=60)
ap.add_argument("--val-b", type=int, default=300)
ap.add_argument("--dry-run", action="store_true", help="only print pool sizes for the chosen --pools; write nothing")
ap.add_argument("--copy-booklets", action="store_true", help="copy PDFs instead of symlinking (if symlinks fail)")
a = ap.parse_args()

src = Path(a.src)


def rd(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


cases = {c["id"]: c for c in rd(src / "cases.jsonl")}
gold = {g["id"]: g["label"] for g in rd(src / "expected-labels.jsonl")}

rows = defaultdict(dict)                       # row index -> {"A": case, "B": case}
for cid, c in cases.items():
    m = re.search(r"row-(\d+)-([AB])$", cid)
    if m:
        rows[int(m.group(1))][m.group(2)] = c

info, seen = {}, set()
for n in sorted(rows):
    r = rows[n]
    anyc = r.get("A") or r["B"]
    date = None
    if "A" in r:
        m = re.search(r"(\d{4}_\d{2}_\d{2})", r["A"]["booklet"]["path"])
        date = m.group(1) if m else None
    ref = r["B"]["reference"]["text"] if "B" in r else ""
    key = (anyc["claim"]["text"], ref, gold[anyc["id"]])
    if key in seen:                            # exact duplicate row: drop
        continue
    seen.add(key)
    srcl = (anyc.get("booklet") or anyc.get("reference"))["language"]
    info[n] = {"group": date or "vote:" + anyc["vote"], "label": gold[anyc["id"]],
               "pair": f"{anyc['claim']['language']}>{srcl}"}

groups = sorted({v["group"] for v in info.values()})
if len(groups) < 3:
    raise SystemExit(f"need >= 3 voting days/groups, found {len(groups)}")
rng = random.Random(a.seed)
rng.shuffle(groups)
fr = [float(x) for x in a.pools.split(",")]
if len(fr) != 3 or any(x <= 0 for x in fr):
    raise SystemExit("--pools must contain three positive proportions")
if not abs(sum(fr) - 1.0) < 1e-9:
    raise SystemExit("--pools must sum to 1.0")
n_dev = max(1, round(len(groups) * fr[0]))
n_val = max(1, round(len(groups) * fr[1]))
pools = {"dev": groups[:n_dev], "val": groups[n_dev:n_dev + n_val], "test": groups[n_dev + n_val:]}
assert pools["test"], "test pool is empty: adjust --pools"


def ordered_rows(pool_groups):
    strata = defaultdict(list)
    for n, v in info.items():
        if v["group"] in pool_groups:
            strata[(v["label"], v["pair"])].append(n)
    for k in strata:
        rng.shuffle(strata[k])
    out, keys = [], sorted(strata)
    while any(strata.values()):
        for k in keys:
            if strata[k]:
                out.append(strata[k].pop())
    return out


order = {p: ordered_rows(set(g)) for p, g in pools.items()}
def describe(pool):
    labs = Counter(info[n]["label"] for n in order[pool])
    return f"{len(pools[pool]):2d} days, {len(order[pool]):4d} rows, labels(0/1/2)={labs[0]}/{labs[1]}/{labs[2]}"


print(f"pools {a.pools} over {len(groups)} voting days/groups, {len(info)} unique rows after dedup:")
for pool, need in (("dev", max(a.dev_a, a.dev_b)), ("val", max(a.val_a, a.val_b)), ("test", 0)):
    warn = f"  <-- WARNING: asked for {need} rows" if need > len(order[pool]) else ""
    print(f"  {pool:4s}: {describe(pool)}{warn}")
if a.dry_run:
    raise SystemExit(0)

want = {"dev_a": ("dev", "A", a.dev_a), "dev_b": ("dev", "B", a.dev_b),
        "val_a": ("val", "A", a.val_a), "val_b": ("val", "B", a.val_b),
        "test_a": ("test", "A", None), "test_b": ("test", "B", None)}

manifest = {"seed": a.seed, "source": str(src),
            "pools": {p: {"voting_days_or_groups": sorted(g), "rows": len(order[p])} for p, g in pools.items()},
            "splits": {}}
for name, (pool, task, size) in want.items():
    ids = [rows[n][task]["id"] for n in order[pool][:size] if task in rows[n]]
    manifest["splits"][name] = ids
    d = Path(a.out_root) / name
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "cases.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(cases[i], ensure_ascii=False) + "\n" for i in ids)
    with open(d / "expected-labels.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps({"id": i, "label": gold[i]}) + "\n" for i in ids)
    link = d / "booklets"
    if (src / "booklets").exists() and task == "A":
        if link.is_symlink() or link.exists():
            link.unlink() if link.is_symlink() else shutil.rmtree(link)
        try:
            if a.copy_booklets:
                raise OSError("copy requested")
            os.symlink(os.path.relpath(src / "booklets", d), link)
        except OSError:
            shutil.copytree(src / "booklets", link)
    labs = Counter(gold[i] for i in ids)
    print(f"{name:7s} n={len(ids):4d} labels(0/1/2)={labs[0]}/{labs[1]}/{labs[2]}  pool={pool}")

Path(a.splits_json).parent.mkdir(parents=True, exist_ok=True)
with open(a.splits_json, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)
print("pools (voting days): " + ", ".join(f"{p}={len(g)}" for p, g in pools.items()) + f" | manifest -> {a.splits_json}")