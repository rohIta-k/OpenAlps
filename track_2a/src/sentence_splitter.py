"""Sentence splitting with stable IDs and PDF page metadata."""

import re

# Common abbreviations that should not end a sentence.
ABBREVIATIONS = (
    "z. B.", "u. a.", "d. h.", "bzw.", "usw.", "ca.",
    "Mrd.", "Mio.", "Dr.", "Prof.", "Nr.", "Art.",
    "p. ex.", "c.-à-d.", "env.", "M.", "Mme.", "MM.", "ecc.", "sig.", "n.", "p.",
    "e.g.", "i.e.", "etc.",
)

_MARKER = "\uE000"
_ABBREVIATION_RE = re.compile( "(?<!\\w)(?:" + "|".join(re.escape(a) for a in sorted(set(ABBREVIATIONS), key=len, reverse=True)) + ")", flags=re.IGNORECASE,)
_CLOSERS = '»”’)\\]"'
_SPLIT_RE = re.compile(r"(?:(?<=[.!?…])" rf"|(?<=[.!?…][{_CLOSERS}])" rf"|(?<=[.!?…][{_CLOSERS}]{{2}}))" r"\s+")

def split_sentences(text: str) -> list[str]:
    """Split text into sentences while preserving common abbreviations."""
    if not text or not text.strip():
        return []
    text = _ABBREVIATION_RE.sub(lambda m: m.group().replace(".", _MARKER), text,)
    parts = _SPLIT_RE.split(text)
    return [ p.replace(_MARKER, ".").strip() for p in parts if p.strip()]

def build_sentence_units( pages: tuple[str, ...], sections_by_page: dict[int, str] | None = None, ) -> list[dict]:
    """Build sentence records with 1-based PDF page numbers. sections_by_page, when available, maps PDF page numbers to section names. Sentence text retains the extracted source wording."""
    units = []
    sentence_number = 1
    for page_number, page_text in enumerate(pages, start=1):
        for sentence in split_sentences(page_text):
            units.append(
                {
                    "id": f"S{sentence_number:05d}",
                    "page": page_number,
                    "section": (sections_by_page.get(page_number) if sections_by_page else None),
                    "text": sentence,
                    "position": len(units),
                }
            )
            sentence_number += 1
    return units
