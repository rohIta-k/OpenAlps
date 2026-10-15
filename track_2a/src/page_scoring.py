"""Score and select relevant PDF pages using a case's vote title."""

import logging
import math
import re
import unicodedata
from collections import Counter

log = logging.getLogger(__name__)

# Conservative stop words for German, French, Italian and English titles.
STOP_WORDS = set("""der die das den dem des ein eine einer eines und oder von vom für mit im in am an auf zu zum zur über unter nach bei ist le la les un une des du de et ou pour avec dans sur au au il lo gli i gli una uno e o di del della dei delle per con the a an and or of for with in on to from by is are""".split())


def normalize(text: str) -> str:
    """Normalize text for matching without removing meaningful words."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def tokenize(text: str) -> list[str]:
    """Return normalized word tokens."""
    return re.findall(r"\b\w+\b", normalize(text))

def distinctive_words(title: str) -> list[str]:
    """Remove short and common words from a vote title."""
    return [word for word in tokenize(title) if len(word) > 2 and word not in STOP_WORDS]

def calculate_idf(pages: tuple[str, ...]) -> dict[str, float]:
    """Calculate word rarity across pages in the booklet."""
    document_frequency = Counter()
    for page in pages:
        document_frequency.update(set(tokenize(page)))
    total_pages = len(pages)
    return {word: math.log(1 + total_pages / (1 + count)) for word, count in document_frequency.items()}

def score_page(page_text: str, title: str, idf: dict[str, float],) -> float:
    """Score a page against a vote title; full-title matches rank first."""
    normalized_title = normalize(title)
    normalized_page = normalize(page_text)
    if not normalized_title or not normalized_page:
        return 0.0
    # Exact normalized phrase match gets the highest score.
    if re.search(rf"(?<!\w){re.escape(normalized_title)}(?!\w)",normalized_page,):
        return 100.0

    words = distinctive_words(title)
    if not words:
        return 0.0
    page_words = set(tokenize(page_text))
    total_weight = sum(idf.get(word, 1.0) for word in words)
    if total_weight == 0:
        return 0.0
    matched_weight = sum(idf.get(word, 1.0) for word in words if word in page_words)

    return 50.0 * matched_weight / total_weight


def score_pages(pages: tuple[str, ...], title: str,) -> list[float]:
    """Score all pages using title-word rarity within this booklet."""
    idf = calculate_idf(pages)
    return [score_page(page, title, idf) for page in pages]


def select_page_blocks(scores: list[float], min_score: float = 15.0, expand_score: float = 5.0,context_pages: int = 1, max_pages: int = 15,) -> list[tuple[int, int]]:
    """
    Select multiple contiguous blocks. Returns inclusive, 1-indexed (start, end) page-number pairs. Falls back to the full booklet if no page meets the threshold.
    """
    if not scores:
        return []
    page_count = len(scores)
    if max(scores) < min_score:
        return [(1, page_count)]
    # Each strong page starts a block, expanded into nearby relevant pages.
    selected = set()
    for index, score in enumerate(scores):
        if score < min_score:
            continue
        start = index
        end = index
        # Expand left through moderately relevant pages.
        while start > 0 and scores[start - 1] >= expand_score:
            start -= 1
        # Expand right through moderately relevant pages.
        while end + 1 < page_count and scores[end + 1] >= expand_score:
            end += 1
        # Include a small context margin.
        start = max(0, start - context_pages)
        end = min(page_count - 1, end + context_pages)
        selected.update(range(start, end + 1))
    # Keep strong matches across the booklet rather than one single window.
    if len(selected) > max_pages:
        anchors = sorted(
            (i for i, score in enumerate(scores) if score >= min_score),
            key=lambda i: scores[i],
            reverse=True,)
        chosen = set()
        # Reserve the highest-scoring pages first.
        for index in anchors:
            if len(chosen) >= max_pages:
                break
            chosen.add(index)
        # Use the remaining budget for nearby context pages.
        remaining = sorted(
            selected - chosen,
            key=lambda i: (
                min(abs(i - anchor) for anchor in anchors),i,
                -scores[i],),)

        for index in remaining:
            if len(chosen) >= max_pages:
                break
            chosen.add(index)
        selected = chosen
    # Convert selected zero-indexed positions into contiguous blocks.
    blocks = []
    for index in sorted(selected):
        if not blocks or index > blocks[-1][1] + 1:
            blocks.append([index, index])
        else:
            blocks[-1][1] = index
    # Public page ranges are 1-indexed.
    return [(start + 1, end + 1)for start, end in blocks]

def select_relevant_pages( pages: tuple[str, ...], title: str, min_score: float = 15.0, expand_score: float = 5.0, context_pages: int = 1, max_pages: int = 15,) -> tuple[list[int], list[float]]:
    """
    Return selected zero-based page indices and scores for every page. The caller should retain original page numbers when constructing evidence.
    """
    scores = score_pages(pages, title)
    blocks = select_page_blocks(scores, min_score=min_score, expand_score=expand_score, context_pages=context_pages, max_pages=max_pages,)

    selected_indices = [pagenum for start, end in blocks for pagenum in range(start, end + 1)]
    log.info("booklet_title=%r selected_pages=%s",title, selected_indices)
    return selected_indices, scores
