"""Entrypoint: python -m src.cli --input /data/cases.jsonl --output /output/predictions.jsonl"""
import argparse
import json
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .clean import clean_cases
from .config import get_settings
from .io_utils import read_cases
from .llm_client import LLMClient
from .pipeline import process_case

log = logging.getLogger("track2a")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Track 2A: claim vs Swiss voting booklet(OST)")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None, help="dev only: first N cases")
    ap.add_argument("--log-file",default="logs/pipeline.log",help="Path to save pipeline logs",)
    a = ap.parse_args(argv)
    log_path = Path(a.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(a.log_file, mode="w", encoding="utf-8"),logging.StreamHandler(sys.stderr),],force=True,)
    log.info("Starting pipeline")
    log.info("Input: %s", a.input)
    log.info("Output: %s", a.output)
    log.info("Log file: %s", log_path)
    st = get_settings()
    cases = list(read_cases(a.input))
    original_count = len(cases)
    cases, duplicate_ids = clean_cases(cases)
    log.info("Input cases: %d | duplicates removed: %d | unique cases: %d",original_count,len(duplicate_ids),len(cases))
    if duplicate_ids:
      log.warning("Duplicate case IDs skipped: %s", duplicate_ids)
    if a.limit is not None:
        cases = cases[: a.limit]
    llm = LLMClient(st)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    lock, done, zero = threading.Lock(), 0, 0

    with open(a.output, "w", encoding="utf-8") as out, ThreadPoolExecutor(a.workers or st.workers) as ex:
        futs = [ex.submit(process_case, c, st, llm) for c in cases]
        for f in as_completed(futs):
            resp = f.result()
            with lock:
                out.write(json.dumps(resp, ensure_ascii=False) + "\n")
                out.flush()
                done += 1
                zero += resp["metrics"]["input_tokens"] == 0
                if done % 10 == 0:
                    log.info("progress %d/%d", done, len(cases))
    log.info("wrote %d predictions -> %s (zero-token/fallback cases: %d)", done, a.output, zero)
    return 0


if __name__ == "__main__":
    sys.exit(main())
