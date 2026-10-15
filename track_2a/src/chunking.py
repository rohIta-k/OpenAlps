"""Fixed-window chunking and sentence-neighbour context."""
from __future__ import annotations


def pack_top_k_context(
    sentence_units: list[dict],
    ranked_sentences: list[dict],
    max_chars: int,
    radius: int = 1,
) -> dict:
    """Expand ranked sentences and pack as much relevant context as fits."""
    if max_chars < 0:
        raise ValueError("max_chars must be non-negative")
    if radius < 0:
        raise ValueError("radius must be non-negative")
    if not sentence_units or not ranked_sentences:
        return {"text": "", "sentences": [], "truncated": False}

    positions = {
        sentence["id"]: index
        for index, sentence in enumerate(sentence_units)
    }

    def render(sentences: list[dict]) -> str:
        parts = []
        current_page = None

        for sentence in sentences:
            page = sentence["page"]

            if page != current_page:
                parts.append(f"[[PAGE {page}]]")
                current_page = page

            parts.append(
                f"[{sentence['id']} p.{page}] {sentence['text']}"
            )

        return "\n".join(parts)

    selected_ids = set()
    truncated = False

    for candidate in ranked_sentences:
        candidate_id = candidate["id"]

        if candidate_id not in positions:
            continue

        center = positions[candidate_id]
        start = center
        end = center

        # Expand left, without crossing gaps in source positions.
        for _ in range(radius):
            previous = start - 1
            if previous < 0:
                break
            if sentence_units[previous]["page"] != sentence_units[center]["page"]:
                break
            if (
                sentence_units[start]["position"]
                != sentence_units[previous]["position"] + 1
            ):
                break
            start = previous

        # Expand right, without crossing gaps in source positions.
        for _ in range(radius):
            following = end + 1
            if following >= len(sentence_units):
                break
            if sentence_units[following]["page"] != sentence_units[center]["page"]:
                break
            if (
                sentence_units[following]["position"]
                != sentence_units[end]["position"] + 1
            ):
                break
            end = following

        neighborhood = sentence_units[start : end + 1]
        trial_ids = selected_ids | {
            sentence["id"] for sentence in neighborhood
        }

        # Render in source order to calculate the exact resulting size.
        trial_sentences = sorted(
            (
                sentence for sentence in sentence_units
                if sentence["id"] in trial_ids
            ),
            key=lambda sentence: sentence["position"],
        )
        trial_text = render(trial_sentences)

        if len(trial_text) > max_chars:
            truncated = True
            continue

        selected_ids = trial_ids

    packed_sentences = sorted(
        (
            sentence for sentence in sentence_units
            if sentence["id"] in selected_ids
        ),
        key=lambda sentence: sentence["position"],
    )

    return {
        "text": render(packed_sentences),
        "sentences": packed_sentences,
        "truncated": truncated,
    }
