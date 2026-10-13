import json

from src.config import Settings
from src.llm_client import LLMResult
from src.pipeline import process_case
from tests.helpers import make_pdf


def settings(tmp_path):
    return Settings("http://x", "k", "m", 1, 300, 600000, 10, str(tmp_path), "/tmp/c", False, True)

class Stub:
    def __init__(self, text, i=111, o=22, responses=None):
        self.text, self.i, self.o = text, i, o
        self.responses = list(responses) if responses is not None else None
        self.calls = 0

    def chat(self, messages, task="A", max_tokens=None):
        self.calls += 1
        text = self.text
        if self.responses is not None:
            text = self.responses.pop(0) if self.responses else self.text
        return LLMResult(text, self.i, self.o)


class Boom:
    def chat(self, messages, task="A", max_tokens=None):
        raise RuntimeError("network down")


def case_a():
    return {"id": "A1", "vote": "Initiative", "claim": {"text": "Der Bundesrat lehnt ab.", "language": "de"},
            "booklet": {"path": "b.pdf", "language": "de"}}


def test_task_a_entailment_with_verified_page(tmp_path):
    make_pdf(tmp_path / "b.pdf")
    quote = "Der Bundesrat empfiehlt, die Initiative abzulehnen, weil sie die Stabilität der Schweiz gefährdet."
    out = process_case(case_a(), settings(tmp_path),
                       Stub(json.dumps({"label": "entailment", "evidence": [{"page": 3, "text": quote}]})))
    assert out["label"] == 0 and out["label_name"] == "entailment"
    assert [e["page"] for e in out["evidence"]] == [3, 2]          # hinted page first, then the other place
    assert out["metrics"]["input_tokens"] == 111 and out["metrics"]["output_tokens"] == 22


def test_task_a_neutral_has_no_evidence(tmp_path):
    make_pdf(tmp_path / "b.pdf")
    out = process_case(case_a(), settings(tmp_path), Stub('{"label":"neutral","evidence":[]}'))
    assert out["label"] == 1 and out["evidence"] == []


def test_task_a_contradiction_gets_page_fallback(tmp_path):
    make_pdf(tmp_path / "b.pdf")
    out = process_case(case_a(), settings(tmp_path),
                       Stub('{"label":"contradiction","evidence":[{"page":2,"text":"erfunden erfunden erfunden erfunden"}]}'))
    assert out["label"] == 2 and out["evidence"][0]["page"] == 2


def test_task_b(tmp_path):
    case = {"id": "B1", "vote": "V", "claim": {"text": "c", "language": "fr"},
            "reference": {"text": "Der Bundesrat empfiehlt die Ablehnung.", "language": "de"}}
    out = process_case(case, settings(tmp_path),
                       Stub('{"label":"entailment","evidence":null}'))
    assert out["label"] == 0
    assert out["evidence"] == []


def test_failure_never_raises_and_unparsable_keeps_tokens(tmp_path):
    make_pdf(tmp_path / "b.pdf")
    stub = Stub("gibberish", i=500, o=5)
    out = process_case(case_a(), settings(tmp_path), stub)
    assert out["label"] == 1
    assert out["metrics"]["input_tokens"] == 1000
    assert out["metrics"]["output_tokens"] == 10
    assert stub.calls == 2


def test_missing_pdf_is_a_fallback_not_a_crash(tmp_path):
    out = process_case(case_a(), settings(tmp_path), Stub('{"label":"neutral","evidence":[]}'))
    assert out["id"] == "A1" and out["label"] == 1


def test_mock_with_real_key_is_flagged_loudly(caplog):
    import logging

    from src.llm_client import LLMClient
    with caplog.at_level(logging.ERROR, logger="track2a"):
        LLMClient(settings("/tmp"))                 # settings() builds mock=True with api_key="k"
    assert "every answer is FAKE" in caplog.text
    
def test_parse_failure_retries_and_recovers(tmp_path):
    make_pdf(tmp_path / "b.pdf")
    stub = Stub( "unused", i=100, o=10, responses=[ '{"evidence":[]}', '{"label":"neutral","evidence":[]}',],)
    out = process_case(case_a(), settings(tmp_path), stub)
    assert out["label"] == 1
    assert out["evidence"] == []
    assert out["metrics"]["input_tokens"] == 200
    assert out["metrics"]["output_tokens"] == 20
    assert stub.calls == 2
