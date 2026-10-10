"""process_case(): one case in, exactly one contract-valid response out (never raises)."""
import logging
import os
import time

from .evidence import build_evidence_a, get_index
from .io_utils import make_response
from .parsing import parse_output
from .pdf_loader import load_pages, render_booklet
from .prompts import TASK_B_MAX_TOKENS, messages_a, messages_b

log = logging.getLogger("track2a")

def _fallback(case_id, t0, reason, in_tok=0, out_tok=0):
    log.error("%s -> fallback neutral (%s)", case_id, reason)
    return make_response(case_id, 1, [], in_tok, out_tok, (time.perf_counter() - t0) * 1000)

def process_case(case, st, llm):
    t0 = time.perf_counter()
    cid, claim, vote = case["id"], case["claim"]["text"], case.get("vote", "")
    clang = case["claim"].get("language", "")
    in_tok = out_tok = 0
    try:
        if "booklet" in case:
            path = os.path.join(st.data_dir, case["booklet"]["path"])
            pages = load_pages(path)
            text, truncated = render_booklet(pages, st.max_input_chars)
            if truncated:
                log.warning("%s: booklet truncated to %d chars", cid, st.max_input_chars)
            res = llm.chat(messages_a(vote, claim, clang, text))
        else:
            source = case["reference"]["text"]
            res = llm.chat(messages_b(vote, claim, clang, source), max_tokens=TASK_B_MAX_TOKENS)
        in_tok, out_tok = res.input_tokens, res.output_tokens
        label, evidence = parse_output(res.text)
        if label is None:
            return _fallback(cid, t0, "unparsable: " + res.text[:80], in_tok, out_tok)
        if "booklet" in case:
            evidence = (build_evidence_a(evidence, get_index(path, pages), require_one=True)
                        if label in (0, 2) else [])
        else:
          evidence = []
        ms = (time.perf_counter() - t0) * 1000
        log.info("%s label=%d in=%d out=%d ms=%d ev=%d", cid, label, in_tok, out_tok, ms, len(evidence))
        return make_response(cid, label, evidence, in_tok, out_tok, ms)
    except Exception as e:
        return _fallback(cid, t0, repr(e)[:200], in_tok, out_tok)
