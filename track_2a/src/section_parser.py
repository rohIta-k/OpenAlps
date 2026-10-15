
"""Detect and parse German, French and Italian voting-booklet contents pages."""

import re
import unicodedata

SECTION_ALIASES = ("In Kürze","En bref", "In breve","Im Detail", "En détail","In dettaglio", "Argumente", "Arguments",  "Gli argomenti", "Abstimmungstext", "Abstimmungstexte","Texte soumis au vote", "Il testo in votazione",)

VOTE_ALIASES = ("Erste Vorlage", "Zweite Vorlage", "Dritte Vorlage", "Vierte Vorlage", "Fünfte Vorlage", "Premier objet", "Deuxième objet", "Troisième objet", "Quatrième objet", "Cinquième objet", "Primo oggetto", "Secondo oggetto", "Terzo oggetto", "Quarto oggetto", "Quinto oggetto",)

TOC_TITLES = ( "Inhaltsverzeichnis", "Table des matières", "Indice", "Sommario",)

_SECTION_LOOKUP = { " ".join(alias.casefold().split()): alias for alias in SECTION_ALIASES}

_VOTE_PATTERN = re.compile(r"^(?:" + "|".join(re.escape(alias) for alias in sorted(VOTE_ALIASES, key=len, reverse=True)) + r")$", re.IGNORECASE,)

_SECTION_ENTRY_PATTERN = re.compile( r"^(.*?)\s+(\d+)(?:\s*[-–—]\s*(\d+))?$")

_IGNORE_LINES = { "die videos zu den abstimmungen:", "die app zu den abstimmungen:", "les vidéos sur la votation :", "l'application sur les votations :", "i video della votazione:", "l'applicazione sulle votazioni:", "voteinfo", "admin.ch/videos-fr", "admin.ch/video_it",}

def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()

def _prepare_text(text: str) -> str:
    """Put vote and section entries on separate lines."""
    text = unicodedata.normalize("NFKC", text).replace("\u00a0", " ")
    aliases = sorted( (*VOTE_ALIASES, *SECTION_ALIASES), key=len,reverse=True,)
    for alias in aliases:
        text = re.sub(re.escape(alias), lambda m: "\n" + m.group(0), text, flags=re.IGNORECASE,)

    return text

def _section_entry(line: str):
    match = _SECTION_ENTRY_PATTERN.fullmatch(line.strip())
    if not match:
        return None
    heading, start_text, end_text = match.groups()
    section = _SECTION_LOOKUP.get(_normalize(heading))
    if section is None:
        return None
    return {
        "section": section,
        "start": int(start_text),
        "end": int(end_text) if end_text else None,
    }


def detect_contents_page( pages: tuple[str, ...], search_pages: int = 12,) -> tuple[int, str, int] | None:
    """Return (zero-based PDF index, text, printed-to-physical offset). Only the first `search_pages` physical pages are scanned. Returns None when no convincing contents page is found."""
    for index, text in enumerate(pages[:search_pages]):
        normalized = _normalize(text)
        prepared = _prepare_text(text)
        lines = [line.strip() for line in prepared.splitlines() if line.strip()]
        section_count = sum(_section_entry(line) is not None for line in lines)
        has_vote_label = any(_VOTE_PATTERN.fullmatch(line) for line in lines)
        has_contents_title = any(_normalize(title) in normalized for title in TOC_TITLES)
        if section_count < 3:
            continue
        if not (has_vote_label or has_contents_title):
            continue
        # Look for a standalone printed page number near the top or bottom.
        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidates = []
        for line in raw_lines[:3] + raw_lines[-3:]:
            if re.fullmatch(r"\d{1,3}", line):
                candidates.append(int(line))
        physical_page = index + 1
        offset = (physical_page - candidates[0] if candidates else 0)
        return index, text, offset
    return None


def parse_toc_sections(toc_text: str, page_count: int, page_offset: int = 0,) -> dict[int, str]:
    """Map 1-based physical PDF page numbers to original-language sections."""
    if not toc_text.strip() or page_count <= 0:
        return {}
    lines = [
        line.strip()
        for line in _prepare_text(toc_text).splitlines()
        if line.strip()
    ]
    current_vote = "Unknown vote"
    title_parts = []
    awaiting_title = False
    entries = []
    for line in lines:
        normalized = _normalize(line)
        if normalized in _IGNORE_LINES:
            continue
        if any(_normalize(title) == normalized for title in TOC_TITLES):
            continue
        if _VOTE_PATTERN.fullmatch(line):
            current_vote = line
            title_parts = []
            awaiting_title = True
            continue
        entry = _section_entry(line)
        if entry:
            if awaiting_title and title_parts:
                current_vote = " ".join(title_parts)
                awaiting_title = False
            entries.append({ "vote": current_vote, **entry,})
            continue
        if awaiting_title and not re.fullmatch(r"\d{1,3}", line):
            title_parts.append(line)
    if not entries:
        return {}
    # Infer missing section ends from the next section in the same vote.
    sections_by_page = {}
    for index, entry in enumerate(entries):
        start = entry["start"]
        if entry["end"] is not None:
            end = entry["end"]
        else:
            following = [
                other["start"]
                for other in entries[index + 1:]
                if other["vote"] == entry["vote"]
                and other["start"] > start
            ]
            end = min(following) - 1 if following else page_count - page_offset
        physical_start = max(1, start + page_offset)
        physical_end = min(page_count, end + page_offset)
        if physical_end < physical_start:
            continue
        label = f'{entry["vote"]} — {entry["section"]}'
        for page in range(physical_start, physical_end + 1):
            sections_by_page[page] = label
    return sections_by_page


def detect_toc_sections(pages: tuple[str, ...], search_pages: int = 12,) -> dict[int, str]:
    """Detect a contents page and parse its section-to-page mapping."""
    detected = detect_contents_page(pages, search_pages=search_pages)
    if detected is None:
        return {}
    _, toc_text, offset = detected
    return parse_toc_sections(toc_text, page_count=len(pages), page_offset=offset,)

def sections_from_outline(outline: list[dict], page_count: int,) -> dict[int, str]:
    """Build section metadata from PDF bookmarks when their titles match known section headings. Bookmark page numbers are physical and 1-based.
    """
    if not outline or page_count <= 0:
        return {}
    recognized = []
    for item in outline:
        title = item.get("title", "").strip()
        page = item.get("page", 0)
        normalized_title = _normalize(title)
        section = _SECTION_LOOKUP.get(normalized_title)
        if section is None or not isinstance(page, int):
            continue
        if not 1 <= page <= page_count:
            continue
        recognized.append((page, title, section))
    recognized.sort(key=lambda item: item[0])
    result = {}
    for index, (start, title, section) in enumerate(recognized):
        next_pages = [ page for page, _, _ in recognized[index + 1:]if page > start]
        end = min(next_pages) - 1 if next_pages else page_count
        label = title
        for page in range(start, end + 1):
            result[page] = label
    return result
