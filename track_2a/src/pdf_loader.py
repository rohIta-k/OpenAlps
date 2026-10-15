"""Page-aware PDF text extraction. Index 0 == PDF page 1."""
import re
import threading
import unicodedata
from functools import lru_cache

import pymupdf

_lock = threading.Lock()

def _clean(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("\u00ad", "")
    t = t.replace("\u00a0", " ")
    # Join words split by a line-break hyphen.
    t = re.sub(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)", "", t)
    t = t.translate(str.maketrans({"\u2018": "'","\u2019": "'", "\u201c": '"',"\u201d": '"',}))
    # Normalize whitespace within lines.
    t = re.sub(r"[ \t]+", " ", t)
    # Join wrapped lines within each paragraph.
    paragraphs = re.split(r"\n\s*\n", t)
    paragraphs = [re.sub(r"\s*\n\s*", " ", p).strip() for p in paragraphs]
    return "\n\n".join(p for p in paragraphs if p)

def _extract_page_text(page) -> str:
    """Extract text block-by-block to preserve headings and columns."""
    blocks = page.get_text("blocks", sort=True)
    parts = []

    for block in blocks:
        x0, y0, x1, y1, text = block[:5]
        if not text.strip():
            continue
        parts.append((y0, x0, text.strip()))

    # Top-to-bottom, then left-to-right for blocks at similar positions.
    parts.sort(key=lambda item: (round(item[0] / 5), item[1]))

    return "\n\n".join(text for _, _, text in parts)

@lru_cache(maxsize=64)
def _load(path: str) -> tuple:
    pages = []
    with pymupdf.open(path) as doc:
        for page in doc:
            pages.append(_clean(_extract_page_text(page)))
    return (tuple(pages))

def load_pages(path: str) -> tuple:
    """Text per page, cached per path (deterministic, so case order cannot matter)."""
    with _lock:
        return _load(path)

@lru_cache(maxsize=64)
def _load_pdf_outline(path: str) -> tuple[tuple[int, str, int], ...]:
    """Return (level, title, physical_page) entries from PDF bookmarks."""
    with pymupdf.open(path) as doc:
        return tuple(
            (int(level), str(title).strip(), int(page))
            for level, title, page in doc.get_toc(simple=True)
            if title and page > 0)

def load_pdf_outline(path: str) -> list[dict]:
    """Extract PDF bookmarks as dictionaries; return [] when none exist."""
    with _lock:
        entries = _load_pdf_outline(path)
    return [
        {"level": level, "title": title, "page": page}
        for level, title, page in entries
    ]

def render_booklet(pages, max_chars: int):
    """Concatenate pages with [[PAGE n]] markers. Returns (text, truncated)."""
    parts, total, truncated = [], 0, False
    for i, t in enumerate(pages, 1):
        chunk = f"[[PAGE {i}]]\n{t}\n"
        if total + len(chunk) > max_chars:
            truncated = True
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n".join(parts), truncated
