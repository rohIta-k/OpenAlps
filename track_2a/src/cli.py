"""Entrypoint: python -m src.cli --input /data/cases.jsonl --output /output/predictions.jsonl"""
import argparse
import json
import logging
import sys
from pathlib import Path

from .config import get_settings
from .io_utils import read_cases
from .llm_client import LLMClient
from .pipeline import process_case

log = logging.getLogger("track2a")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Track 2A: claim vs Swiss voting booklet(OST)")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--log-file",default="stderr",help="Path to save pipeline logs",)
    a = ap.parse_args(argv)
    handlers = [logging.StreamHandler(sys.stderr)]
    if a.log_file != "stderr":
      log_path = Path(a.log_file)
      log_path.parent.mkdir(parents=True, exist_ok=True)
      handlers.append(logging.FileHandler(log_path, mode="w", encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers,force=True,)
    log.info("Starting pipeline")
    log.info("Input: %s", a.input)
    log.info("Output: %s", a.output)
    if a.log_file == "stderr":
      log.info("File logging disabled; writing logs to stderr")
    else:
      log.info("Log file: %s", log_path)
    st = get_settings()
    cases = list(read_cases(a.input))
    log.info("Input cases: %d | processing all cases without deduplication", len(cases))
    llm = LLMClient(st)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    done =0
    zero = 0
    with open(a.output, "w", encoding="utf-8") as out:
      for c in cases:
        resp = process_case(c, st, llm)
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
