from src.evidence import PageIndex, build_evidence_a, squash_map

PAGES = (
    "Seite eins mit Einleitung.",
    "Die Beschaffung der Kampf-\nflugzeuge  ist  Sache des Bundes und wird\nvom Parlament beschlossen.",
    "Die Beschaffung der Kampfflugzeuge ist Sache des Bundes und wird vom Parlament beschlossen.",
)

def test_squash_map_indices_point_to_original_chars():
    s, idx = squash_map("Ab-\nC 1")
    assert s == "abc1" and [("Ab-\nC 1")[i] for i in idx] == ["A", "b", "C", "1"]


def test_locate_ignores_hyphenation_and_returns_pdf_text_span():
    hits = PageIndex(PAGES).locate("Die Beschaffung der Kampfflugzeuge ist Sache des Bundes")
    assert [p for p, _ in hits] == [2, 3]                      # the same fact on two pages -> two items
    assert "Kampf-\nflugzeuge" in hits[0][1]                   # span is the PDF's own text


def test_hint_goes_first_and_short_quotes_are_rejected():
    idx = PageIndex(PAGES)
    assert idx.locate("Die Beschaffung der Kampfflugzeuge ist Sache des Bundes", hint=3)[0][0] == 3
    assert idx.locate("Bundes") == []


def test_build_a_fallback_to_page_text_when_unverifiable():
    ev = build_evidence_a([{"page": 2, "text": "ein erfundenes Zitat ohne Treffer im Dokument"}],
                          PageIndex(PAGES), require_one=True)
    assert len(ev) == 1 and ev[0]["page"] == 2 and "Kampf" in ev[0]["text"]


def test_build_a_no_fallback_when_not_required():
    assert build_evidence_a([{"page": 2, "text": "erfunden erfunden erfunden erfunden"}],
                            PageIndex(PAGES), require_one=False) == []
