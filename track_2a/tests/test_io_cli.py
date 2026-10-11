import json
import subprocess
import sys

from src.cli import main
from src.io_utils import read_cases
from tests.helpers import make_pdf


def write_cases(tmp_path):
    cases = [
        {"id": "x-A", "vote": "V", "claim": {"text": "c", "language": "de"}, "booklet": {"path": "b.pdf", "language": "de"}},
        {"id": "x-B", "vote": "V", "claim": {"text": "c", "language": "it"}, "reference": {"text": "r", "language": "fr"}},
    ]
    p = tmp_path / "cases.jsonl"
    p.write_text("\n".join(json.dumps(c) for c in cases) + "\n{broken\n\n" +
                 json.dumps({"id": "bad", "claim": {"text": "c"}, "booklet": {}, "reference": {}}) + "\n")
    return p

def test_read_cases_skips_invalid(tmp_path):
    assert [c["id"] for c in read_cases(write_cases(tmp_path))] == ["x-A", "x-B"]

def test_cli_mock_end_to_end_and_validator(tmp_path, monkeypatch):
    make_pdf(tmp_path / "b.pdf")
    cases, out = write_cases(tmp_path), tmp_path / "out" / "predictions.jsonl"
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert main(["--input", str(cases), "--output", str(out)]) == 0
    assert len(out.read_text().strip().splitlines()) == 2
    clean = tmp_path / "clean.jsonl"
    clean.write_text("\n".join(cases.read_text().splitlines()[:2]) + "\n")
    r = subprocess.run([sys.executable, "scripts/validate_output.py", "--cases", str(clean),
                        "--predictions", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
