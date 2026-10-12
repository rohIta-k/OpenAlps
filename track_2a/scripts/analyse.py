"""Create a detailed error-analysis report for Task A and Task B."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

from rapidfuzz import fuzz

LABELS = ["entailment", "neutral", "contradiction"]
INVALID = -1
MAX_QUOTES = 5
MAX_QUOTE_CHARS = 5000
DEFAULT_THRESHOLD = 75.0

def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def normalize(text):
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def task_of(case_id, case):
    if case:
        return "A" if "booklet" in case else "B"
    return case_id.rsplit("-", 1)[-1]


def label_of(prediction):
    if not prediction:
        return INVALID
    label = prediction.get("label")
    if (not isinstance(label, int) or isinstance(label, bool) or label not in range(3)):
        return INVALID
    if prediction.get("label_name") != LABELS[label]:
        return INVALID
    return label


def evidence_scores(prediction, reference, threshold, max_chars):
    """Score each of the first five evidence quotes against the gold passage."""
    evidence = prediction.get("evidence") if prediction else None
    if not isinstance(evidence, list):
        evidence = []
    details = []
    reference_normalized = normalize(reference) if isinstance(reference, str) else ""
    for index, item in enumerate(evidence[:MAX_QUOTES], start=1):
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            details.append({
                "rank": index,
                "quote": item,
                "fuzzy_score": None,
                "eligible": False,
                "matches_threshold": False,
                "reason": "Invalid evidence item",
            })
            continue
        quote = item["text"]
        normalized_quote = normalize(quote)
        if not normalized_quote:
            score = None
            reason = "Empty evidence quote"
        elif len(normalized_quote) > max_chars:
            score = None
            reason = f"Quote exceeds {max_chars} characters"
        elif not reference_normalized:
            score = None
            reason = "Gold reference passage missing or empty"
        else:
            score = round(fuzz.partial_ratio(normalized_quote, reference_normalized), 2)
            reason = None
        details.append({
            "rank": index,
            "page": item.get("page"),
            "quote": quote,
            "fuzzy_score": score,
            "eligible": score is not None,
            "matches_threshold": (score is not None and score >= threshold),
            "reason": reason,
        })
    eligible_scores = [item["fuzzy_score"] for item in details if item["fuzzy_score"] is not None]
    best_score = max(eligible_scores, default=None)
    matched = best_score is not None and best_score >= threshold
    return {
        "threshold": threshold,
        "best_fuzzy_score": best_score,
        "matched_threshold": matched,
        "quotes_checked": len(details),
        "evidence": details,
    }

def main():
    parser = argparse.ArgumentParser(description="Find label errors and weak Task A evidence.")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--cases",type=Path,required=True,help="Original cases.jsonl for full claim and language details",)
    parser.add_argument( "--output", type=Path,required=True,help="Report path, e.g. analysis/errors.json",)
    parser.add_argument( "--min-ratio",type=float,default=DEFAULT_THRESHOLD,help="Minimum fuzzy-match score (default: 75)",)
    parser.add_argument("--max-quote-chars",type=int,default=MAX_QUOTE_CHARS)
    args = parser.parse_args()
    if not 0 <= args.min_ratio <= 100:
        parser.error("--min-ratio must be between 0 and 100")

    expected = {row["id"]: row for row in read_jsonl(args.expected)}
    cases = {row["id"]: row for row in read_jsonl(args.cases)}

    predictions = {}
    duplicate_ids = set()
    unknown_ids = []

    for prediction in read_jsonl(args.predictions):
        case_id = prediction.get("id")
        if case_id not in expected:
            unknown_ids.append(case_id)
            continue
        if case_id in predictions:
            duplicate_ids.add(case_id)
        else:
            predictions[case_id] = prediction

    # Exclude ambiguous duplicate predictions instead of silently choosing one.
    for case_id in duplicate_ids:
        predictions[case_id] = None

    task_b_errors = []
    task_a_errors = []

    for case_id, gold in expected.items():
        case = cases.get(case_id)
        task = task_of(case_id, case)
        prediction = predictions.get(case_id)
        expected_label = gold.get("label")
        predicted_label = label_of(prediction)
        label_mismatch = predicted_label != expected_label
        record = {
            "id": case_id,
            "task": task,
            "error_types": [],
            "expected_label": expected_label,
            "expected_label_name": (LABELS[expected_label] if isinstance(expected_label, int) and not isinstance(expected_label, bool) and expected_label in range(3) else None),
            "predicted_label": (predicted_label if predicted_label != INVALID else None),
            "predicted_label_name": (LABELS[predicted_label] if predicted_label != INVALID else None),
            "label_mismatch": label_mismatch,
            "gold_reference": gold.get("reference"),
            "case": case,
            "prediction": prediction,
        }
        if prediction is None:
            record["error_types"].append("missing_or_duplicate_prediction")
        elif predicted_label == INVALID:
            record["error_types"].append("invalid_prediction_label")
        if task == "B":
            if label_mismatch:
                record["error_types"].append("label_mismatch")
                task_b_errors.append(record)
        elif task == "A":
            needs_evidence = expected_label != 1
            scores = None
            if needs_evidence:
                scores = evidence_scores(prediction,gold.get("reference"),args.min_ratio,args.max_quote_chars)
                record["evidence_analysis"] = scores
            evidence_failure = (needs_evidence and (scores["best_fuzzy_score"] is None or not scores["matched_threshold"]))

            if label_mismatch:
                record["error_types"].append("label_mismatch")
            if evidence_failure:
                record["error_types"].append("evidence_below_threshold")

            if label_mismatch or evidence_failure:
                task_a_errors.append(record)

    report = {
        "config": {
            "predictions": str(args.predictions),
            "expected": str(args.expected),
            "cases": str(args.cases),
            "fuzzy_threshold": args.min_ratio,
            "max_quote_chars": args.max_quote_chars,
            "max_quotes_checked": MAX_QUOTES,
        },
        "summary": {
            "expected_cases": len(expected),
            "prediction_records": len(read_jsonl(args.predictions)),
            "task_b_label_errors": len(task_b_errors),
            "task_a_flagged_cases": len(task_a_errors),
            "task_a_label_errors": sum(item["label_mismatch"] for item in task_a_errors),
            "task_a_evidence_failures": sum("evidence_below_threshold" in item["error_types"]for item in task_a_errors),
            "duplicate_prediction_ids": sorted(duplicate_ids),
            "unknown_prediction_ids": unknown_ids,
        },
        "task_b_label_errors": task_b_errors,
        "task_a_errors": task_a_errors,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",encoding="utf-8",)
    print(f"Analysis report written to: {args.output}")
    print(f"Task B label errors: {len(task_b_errors)}")
    print(f"Task A flagged cases: {len(task_a_errors)}")
    print("Task A label errors: "f"{report['summary']['task_a_label_errors']}")
    print("Task A evidence failures: "f"{report['summary']['task_a_evidence_failures']}")


if __name__ == "__main__":
    main()
