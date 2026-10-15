"""process_case(): one case in, exactly one contract-valid response out (never raises)."""
import logging
import os
import time

from .evidence import build_evidence_a, get_index
from .io_utils import make_response
from .page_scoring import select_relevant_pages
from .parsing import parse_output_detailed
from .pdf_loader import load_pages
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
            selected_pages, scores = select_relevant_pages(pages, vote)
            # Build the prompt using original PDF page numbers.
            parts = []
            total_chars = 0
            truncated = False
            for page_num in selected_pages:
                chunk = f"[[PAGE {page_num}]]\n{pages[page_num - 1]}\n"
                if total_chars + len(chunk) > st.max_input_chars:
                  truncated = True
                  break
                parts.append(chunk)
                total_chars += len(chunk)
            if truncated:
                log.warning("%s: selected booklet pages truncated at %d chars",cid,st.max_input_chars,)
            text = "\n".join(parts)
            messages = messages_a(vote, claim, clang, text)
            task = "A"
            max_tokens = None
        else:
            source = case["reference"]["text"]
            messages = messages_b(vote, claim, clang, source)
            task = "B"
            max_tokens = TASK_B_MAX_TOKENS
        res = llm.chat(messages, task=task, max_tokens=max_tokens)
        in_tok+= res.input_tokens
        out_tok+= res.output_tokens
        label, evidence,error = parse_output_detailed(res.text)
        if error:
            log.warning("%s task=%s parse_failure=%s; retrying once",cid, task, error)
            retry_messages = [dict(m) for m in messages]
            retry_instruction = ("Your previous response failed JSON validation: "f"{error}. Return a complete JSON object matching the ""required schema exactly. Include every required field, ""use a valid label, and do not include any extra text.")
            retry_messages[-1] = { **retry_messages[-1],"content": retry_messages[-1]["content"] + "\n\nCORRECTION:\n"+ retry_instruction,}
            try:
                retry_res = llm.chat(retry_messages, task=task, max_tokens=max_tokens)
                in_tok += retry_res.input_tokens
                out_tok += retry_res.output_tokens
                label, evidence, retry_error = parse_output_detailed(retry_res.text)
                if retry_error:
                    log.error("%s task=%s retry_failed=%s raw_response=%r",cid, task, retry_error, retry_res.text[:300],)
                    return _fallback(cid, t0,f"unparsable_after_retry: {retry_error}",in_tok, out_tok,)
                log.info("%s task=%s parse_retry=recovered", cid, task)
            except Exception:
                log.exception("%s task=%s retry_request_failed", cid, task)
                return _fallback(cid, t0, "retry_request_failed", in_tok, out_tok)

        if "booklet" in case:
            evidence = (build_evidence_a(evidence, get_index(path, pages), require_one=True)
                        if label in (0, 2) else [])
        else:
          evidence = []
        ms = (time.perf_counter() - t0) * 1000
        log.info("%s label=%d in=%d out=%d ms=%d ev=%d", cid, label, in_tok, out_tok, ms, len(evidence))
        return make_response(cid, label, evidence, in_tok, out_tok, ms)
    except Exception as e:
        log.exception("%s: case processing failed", cid)
        return _fallback(cid, t0, repr(e)[:200], in_tok, out_tok)
