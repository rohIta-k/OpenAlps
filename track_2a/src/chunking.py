"""Fixed-window chunking and sentence-neighbour context."""
from __future__ import annotations

def _make_group(sentences: list[dict], group_id: str) -> dict:
    """Build a chunk while preserving its source sentence metadata."""
    return {
        "id": group_id,
        "sentence_ids": [s["id"] for s in sentences],
        "pages": sorted({s["page"] for s in sentences}),
        "sections": list(dict.fromkeys(
            s["section"] for s in sentences if s.get("section")
        )),
        "sentences": sentences,
        "text": " ".join(s["text"] for s in sentences),
    }


def build_sentence_neighborhoods(
    sentence_units: list[dict],
    radius: int = 1,
) -> list[dict]:
    """Create one context unit per sentence, including nearby sentences.

    A radius of 1 includes the previous sentence, the current sentence,
    and the next sentence when they are consecutive in the source.
    """
    if radius < 0:
        raise ValueError("radius must be non-negative")

    neighborhoods = []

    for i, sentence in enumerate(sentence_units):
        start = i
        end = i + 1

        # Expand left only across consecutive source positions.
        for _ in range(radius):
            candidate = start - 1
            if candidate < 0:
                break
            if (
                sentence_units[start]["position"]
                != sentence_units[candidate]["position"] + 1
            ):
                break
            start = candidate

        # Expand right only across consecutive source positions.
        for _ in range(radius):
            candidate = end
            if candidate >= len(sentence_units):
                break
            if (
                sentence_units[candidate]["position"]
                != sentence_units[end - 1]["position"] + 1
            ):
                break
            end += 1

        group = _make_group(
            sentence_units[start:end],
            f"N{sentence['id']}",
        )
        group["center_sentence_id"] = sentence["id"]
        neighborhoods.append(group)

    return neighborhoods


def merge_overlapping_neighborhoods(
    neighborhoods: list[dict],
) -> list[dict]:
    """Merge overlapping neighborhoods without duplicating sentences."""
    if not neighborhoods:
        return []

    merged = []
    current = list(neighborhoods[0]["sentences"])

    for neighborhood in neighborhoods[1:]:
        next_sentences = neighborhood["sentences"]
        current_ids = {s["id"] for s in current}
        next_ids = {s["id"] for s in next_sentences}

        if current_ids & next_ids:
            # Preserve source order and add only unseen sentences.
            for sentence in next_sentences:
                if sentence["id"] not in current_ids:
                    current.append(sentence)
                    current_ids.add(sentence["id"])
            current.sort(key=lambda s: s["position"])
        else:
            merged.append(_make_group(
                current, f"M{len(merged) + 1:05d}"
            ))
            current = list(next_sentences)

    merged.append(_make_group(current, f"M{len(merged) + 1:05d}"))
    return merged
