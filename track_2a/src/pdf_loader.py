"""Page-aware PDF text extraction. Index 0 == PDF page 1."""
import re
import threading
import unicodedata
from functools import lru_cache

from pypdf import PdfReader

_lock = threading.Lock()

def _clean(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("\u00ad", "")                 # soft hyphens
    t = t.replace("\u00a0", " ")
    # Join words split by a line-break hyphen.
    t = re.sub(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)", "", t)
    t = t.translate(str.maketrans({"\u2018": "'", "\u2019": "'","\u201c": '"',"\u201d": '"'}))
    t = re.sub(r"[^\S\r\n]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


@lru_cache(maxsize=64)
def _load(path: str) -> tuple:
    reader = PdfReader(path)
    return tuple(_clean(p.extract_text() or "") for p in reader.pages)


def load_pages(path: str) -> tuple:
    """Text per page, cached per path (deterministic, so case order cannot matter)."""
    with _lock:
        return _load(path)


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
