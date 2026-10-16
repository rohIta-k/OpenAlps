"""Decode and validate structured model responses."""
import json
import logging

logger = logging.getLogger(__name__)

NAMES = ["entailment", "neutral", "contradiction"]

def parse_output_detailed(text: str):
    """Return (label_id | None, evidence, error_reason)."""
    if not text:
        return None, [], "empty_response"
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        return None, [], f"invalid_json: {exc}"
    if not isinstance(obj, dict):
        return None, [], "response_not_object"
    if "label" not in obj:
        return None, [], "missing_label"
    label = str(obj["label"]).strip().lower()
    if label not in NAMES:
        return None, [], f"invalid_label: {label!r}"
    if "evidence" not in obj:
        return None, [], "missing_evidence_field"
    evidence = obj["evidence"]
    # Task B: null becomes an empty list for downstream consistency.
    if evidence is None:
        return NAMES.index(label), [], None
    if not isinstance(evidence, list):
        return None, [], "evidence_not_list_or_null"
    validated = []
    for i, item in enumerate(evidence):
        if not isinstance(item, dict):
            return None, [], f"evidence_item_{i}_not_object"
        page = item.get("page")
        quote = item.get("text")
        if (isinstance(page, bool) or not isinstance(page, int) or page < 1 or not isinstance(quote, str) or not quote.strip() or len(quote) > 5000):
            return None, [], f"evidence_item_{i}_invalid_fields"
        validated.append({"page": page, "text": quote})

    if label != "neutral" and not validated:
        return None, [], "non_neutral_missing_evidence"
    if label == "neutral" and validated:
        logger.warning("Model returned evidence for neutral label; discarding %d evidence item(s)", len(validated))
        return NAMES.index(label), [], None
    if len(validated) > 5:
        return None, [], "too_many_evidence_items"
    return NAMES.index(label), validated, None

def parse_output(text: str):
    """Backward-compatible parser returning (label_id | None, evidence)."""
    label, evidence, _ = parse_output_detailed(text)
    return label, evidence
