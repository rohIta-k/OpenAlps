"""Decode and validate structured model responses."""

import json

NAMES = ["entailment", "neutral", "contradiction"]

def parse_output(text: str):
    """Return (label_id | None, evidence).
    Evidence format:
      Task A: [{"page": int, "text": str}, ...]
      Task B: []
    """
    if not text:
        return None, []

    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None, []
    if not isinstance(obj, dict):
        return None, []

    label = str(obj.get("label", "")).strip().lower()
    if label not in NAMES:
        return None, []

    evidence = obj.get("evidence")

    # Task B: null becomes an empty list for downstream consistency.
    if evidence is None:
        return NAMES.index(label), []

    if not isinstance(evidence, list):
        return None, []

    validated = []

    for item in evidence:
        if not isinstance(item, dict):
            return None, []

        page = item.get("page")
        quote = item.get("text")

        if (
            isinstance(page, bool)
            or not isinstance(page, int)
            or page < 1
            or not isinstance(quote, str)
            or not quote.strip()
            or len(quote) > 5000
        ):
            return None, []

        validated.append({
            "page": page,
            "text": quote,
        })

    # Task A requires evidence for non-neutral predictions.
    if label != "neutral" and not validated:
        return None, []

    if label == "neutral" and validated:
        return None, []

    if len(validated) > 5:
        return None, []

    return NAMES.index(label), validated
