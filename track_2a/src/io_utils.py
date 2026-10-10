"""Reading cases and building contract-valid responses."""
import json
import logging

log = logging.getLogger("track2a")
LABEL_NAMES = {0: "entailment", 1: "neutral", 2: "contradiction"}

def read_cases_checked(path):
    """Return (valid_cases, rejected). rejected = [(case_id or None, reason)]."""
    valid, rejected = [], []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except json.JSONDecodeError as e:
                rejected.append((None, f"line {n}: invalid JSON ({e.msg})"))
                continue
            cid = c.get("id") if isinstance(c, dict) else None
            cid = cid if isinstance(cid, str) and cid else None
            try:
                assert cid, "missing id"
                assert ("booklet" in c) != ("reference" in c), "need exactly one of booklet/reference"
                assert c["claim"]["text"], "empty claim"
                valid.append(c)
            except Exception as e:  # noqa: BLE001
                rejected.append((cid, f"line {n}: {e!r}"))
    return valid, rejected


def read_cases(path):
    """Yield valid case dicts only (rejected lines are logged)."""
    valid, rejected = read_cases_checked(path)
    for cid, why in rejected:
        log.error("skipping invalid input (id=%s): %s", cid, why)
    yield from valid


def make_response(case_id, label, evidence, in_tok, out_tok, ms):
    label = int(label)
    return {
        "id": case_id,
        "label": label,
        "label_name": LABEL_NAMES[label],
        "evidence": evidence,
        "metrics": {
            "input_tokens": int(in_tok),
            "output_tokens": int(out_tok),
            "inference_time_ms": int(ms),
        },
    }
