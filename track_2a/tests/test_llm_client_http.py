"""Integration test of the real OpenAI client path against a local fake OpenAI-compatible server."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.cli import main
from src.config import get_settings
from src.llm_client import LLMClient
from tests.helpers import PAGES, make_pdf

QUOTE = PAGES[1].split(". ")[0] + "."


class Handler(BaseHTTPRequestHandler):
    calls = 0
    seen = []

    def do_POST(self):
        Handler.calls += 1
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Handler.seen.append(body)
        if Handler.calls == 1:                                   # first call: rate limited -> client must retry
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": {"message": "slow down"}}')
            return
        content = json.dumps({"label": "entailment", "evidence": [{"page": 2, "text": QUOTE}]})
        out = {"id": "x", "object": "chat.completion", "created": 0, "model": body["model"],
               "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
               "usage": {"prompt_tokens": 123, "completion_tokens": 17, "total_tokens": 140}}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def start():
    Handler.calls, Handler.seen = 0, []
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_client_retries_on_429_and_reads_usage(monkeypatch):
    srv = start()
    monkeypatch.setenv("BASE_URL", f"http://127.0.0.1:{srv.server_port}/v1")
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("MOCK_LLM", raising=False)
    res = LLMClient(get_settings()).chat([{"role": "user", "content": "hi"}], max_tokens=33)
    srv.shutdown()
    assert (res.input_tokens, res.output_tokens) == (123, 17)
    assert Handler.calls == 2 and Handler.seen[-1]["max_tokens"] == 33 and Handler.seen[-1]["temperature"] == 0


def test_cli_end_to_end_over_http(tmp_path, monkeypatch):
    srv = start()
    make_pdf(tmp_path / "b.pdf")
    cases = tmp_path / "cases.jsonl"
    cases.write_text(json.dumps({"id": "a-A", "vote": "V", "claim": {"text": "c", "language": "de"},
                                 "booklet": {"path": "b.pdf", "language": "de"}}) + "\n")
    monkeypatch.setenv("BASE_URL", f"http://127.0.0.1:{srv.server_port}/v1")
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("MOCK_LLM", raising=False)
    out = tmp_path / "pred.jsonl"
    assert main(["--input", str(cases), "--output", str(out)]) == 0
    srv.shutdown()
    r = json.loads(out.read_text())
    assert r["label"] == 0 and r["evidence"][0]["page"] == 2
    assert r["metrics"]["input_tokens"] == 123 and r["metrics"]["output_tokens"] == 17
    assert "[[PAGE 2]]" in Handler.seen[-1]["messages"][1]["content"]
