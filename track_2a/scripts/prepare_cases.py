"""Generate benchmark inputs from the public Hugging Face dataset."""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

DATASET_VERSION = "v1.1"
DATASET_URL = (
    "https://huggingface.co/datasets/OSTswiss/MNLIoverSwissVotingBooklets/resolve/"
    f"main/{DATASET_VERSION}.jsonl"
)


def download(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--task", choices=["A", "B", "both"], default="both")
    parser.add_argument("--limit", type=int, help="Use only the first N dataset rows")
    parser.add_argument("--download-booklets", action="store_true", help="Also download task A PDFs")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    rows = [json.loads(line) for line in download(DATASET_URL).decode("utf-8").splitlines()]
    tasks = ["A", "B"] if args.task == "both" else [args.task]
    cases, expected_labels = [], []
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for index, row in enumerate(rows[:args.limit]):
        filename = (
            row["booklet_publish_date"].replace("-", "_")
            + "_" + row["reference_language"] + ".pdf"
        )
        if "A" in tasks and args.download_booklets:
            pdf_path = args.output_dir / "booklets" / filename
            if not pdf_path.exists():
                pdf = download(row["booklet_url"])
                if not pdf.startswith(b"%PDF"):
                    raise ValueError(f"Not a PDF: {row['booklet_url']}")
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                pdf_path.write_bytes(pdf)

        for task in tasks:
            case = {
                "id": f"{DATASET_VERSION}-row-{index}-{task}",
                "vote": row["vote"],
                "claim": {"text": row["claim"], "language": row["claim_language"]},
            }
            if task == "A":
                case["booklet"] = {
                    "path": f"booklets/{filename}",
                    "language": row["reference_language"],
                }
            else:
                case["reference"] = {
                    "text": row["reference_string"],
                    "language": row["reference_language"],
                }
            cases.append(case)
            expected = {"id": case["id"], "label": row["entailment_label"]}
            # Gold evidence for scoring citations. Neutral rows pair the claim with an
            # unrelated passage, so they have none.
            if row["entailment_label"] != 1:
                expected["reference"] = row["reference_string"]
            expected_labels.append(expected)

    for filename, records in [
        ("cases.jsonl", cases), ("expected-labels.jsonl", expected_labels)
    ]:
        with (args.output_dir / filename).open("w", encoding="utf-8") as output:
            for record in records:
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(cases)} cases and separate expected labels to {args.output_dir}")


if __name__ == "__main__":
    main()
