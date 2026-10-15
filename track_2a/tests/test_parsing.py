from src.parsing import parse_output


def test_json_with_valid_evidence():
    lab, evidence = parse_output('{"label":"contradiction","evidence":[{"page":4,"text":"abc"}]}')
    assert lab == 2
    assert evidence == [{"page": 4, "text": "abc"}]

def test_task_b_null_evidence():
    assert parse_output('{"label":"entailment","evidence":null}') == (0, [])

def test_neutral_with_empty_evidence():
    assert parse_output('{"label":"neutral","evidence":[]}') == (1, [])

def test_invalid_json_and_prose():
    assert parse_output("The answer is NEUTRAL.") == (None, [])
    assert parse_output("no idea") == (None, [])
    assert parse_output("") == (None, [])
    assert parse_output(None) == (None, [])

def test_invalid_evidence_item():
    assert parse_output('{"label":"contradiction","evidence":[{"page":4,"text":"abc"},"def"]}') == (None, [])

def test_non_neutral_without_evidence():
    assert parse_output('{"label":"entailment","evidence":[]}') == (None, [])

def test_neutral_with_evidence():
    assert parse_output('{"label":"neutral","evidence":[{"page":1,"text":"abc"}]}') == (1, [])

def test_invalid_page_number():
    assert parse_output('{"label":"entailment","evidence":[{"page":0,"text":"abc"}]}') == (None, [])

def test_unknown_label():
    assert parse_output('{"label":"unknown","evidence":[]}') == (None, [])
