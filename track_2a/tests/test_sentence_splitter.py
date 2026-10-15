import pytest

from src.sentence_splitter import build_sentence_units, split_sentences


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Die Vorlage wird angenommen. Sie tritt später in Kraft.",
            ["Die Vorlage wird angenommen.", "Sie tritt später in Kraft."],
        ),
        (
            "Das kostet ca. 5 Mio. Franken. Die Kosten steigen.",
            ["Das kostet ca. 5 Mio. Franken.", "Die Kosten steigen."],
        ),
        (
            "Zum Beispiel: z. B. gilt diese Regel. Danach folgt eine Ausnahme.",
            [
                "Zum Beispiel: z. B. gilt diese Regel.",
                "Danach folgt eine Ausnahme.",
            ],
        ),
        (
            "Cette règle s'applique, p. ex. aux communes. Le vote suit.",
            [
                "Cette règle s'applique, p. ex. aux communes.",
                "Le vote suit.",
            ],
        ),
        (
            "La loi s'applique. M. Dupont présente le rapport. Le vote suit.",
            [
                "La loi s'applique.",
                "M. Dupont présente le rapport.",
                "Le vote suit.",
            ],
        ),
        (
            "La proposta è approvata. La legge entra in vigore.",
            ["La proposta è approvata.", "La legge entra in vigore."],
        ),
        (
            "Er sagte: «Ja.» Danach ging er.",
            ["Er sagte: «Ja.»", "Danach ging er."],
        ),
    ],
)
def test_split_sentences(text, expected):
    assert split_sentences(text) == expected

def test_empty_text_returns_no_sentences():
    assert split_sentences("") == []
    assert split_sentences("   ") == []

def test_sentence_units_have_stable_ids_and_page_metadata():
    pages = ("Erster Satz. Zweiter Satz.", "Troisième phrase. Quarta frase.",)
    sections = {1: "Introduction", 2: "Arguments"}
    units = build_sentence_units(pages, sections)
    assert [unit["id"] for unit in units] == [ "S00001", "S00002", "S00003", "S00004"]
    assert [unit["page"] for unit in units] == [1, 1, 2, 2]
    assert [unit["section"] for unit in units] == ["Introduction","Introduction","Arguments", "Arguments",]
    assert [unit["text"] for unit in units] == [ "Erster Satz.", "Zweiter Satz.", "Troisième phrase.","Quarta frase.", ]

def test_empty_page_preserves_original_page_numbers():
    units = build_sentence_units( ("Ein Satz.", "", "Ein weiterer Satz."))
    assert [unit["id"] for unit in units] == ["S00001", "S00002"]
    assert [unit["page"] for unit in units] == [1, 3]

def test_sections_are_optional():
    units = build_sentence_units(("Ein Satz.",))
    assert units[0]["section"] is None
