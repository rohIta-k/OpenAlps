"""Runtime deduplication using input data."""
import re
import unicodedata


def normalize(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "")
    return re.sub(r"\s+", " ", text).strip().casefold()

def clean_cases(cases):
    """Returns: (unique_cases, duplicate_ids)"""
    seen = set()
    unique_cases = []
    duplicate_ids = []
    for case in cases:
        claim = case.get("claim", {})
        is_task_a = "booklet" in case
        task = "A" if is_task_a else "B"
        vote = normalize(case.get("vote", ""))
        claim_text = normalize(claim.get("text", ""))
        claim_language = normalize(claim.get("language", ""))
        if is_task_a:
            source = case.get("booklet", {})
            source_key = normalize(source.get("path", ""))
            source_language = normalize(source.get("language", ""))
            key = (task, vote, source_key, source_language, claim_language,claim_text)
        else:
            source = case.get("reference", {})
            source_text = normalize(source.get("text", ""))
            source_language = normalize(source.get("language", ""))
            key = (task, vote, source_language, source_text, claim_language, claim_text)

        if key in seen:
            duplicate_ids.append(case.get("id"))
            continue
        seen.add(key)
        unique_cases.append(case)

    return unique_cases, duplicate_ids
