# Data
This directory contains the input data for Track 2A, including the smoke-test sample, public dataset, and custom evaluation data.
## 1. Data layout

The **recommended location** for your dataset is directly inside `data/`. This lets you use the default Makefile commands without specifying a custom data path.

```text
track_2a/
├── data/
│   ├── README.md
│   ├── cases.jsonl              # Default input
│   ├── booklets/                # PDFs referenced by cases.jsonl
│   ├── sample/                  # Committed smoke-test data
│   │   ├── cases.jsonl
│   │   ├── expected-labels.jsonl
│   │   └── booklets/
│   ├── full/                    # Generated full dataset
│   ├── dev_a/  dev_b/            # Development slices
│   ├── val_a/  val_b/            # Validation slices
│   └── test_a/ test_b/           # Held-out test slices
├── docs/
│   └── splits.json
└── scripts/
    └── prepare_cases.py
```

Only `data/sample/` is committed. Generated datasets, downloaded PDFs, model weights, logs, and other generated artifacts are excluded from Git where configured.

## 2. Dataset source

The public source dataset is [`OSTswiss/MNLIoverSwissVotingBooklets`](https://huggingface.co/datasets/OSTswiss/MNLIoverSwissVotingBooklets), specifically `v1.1.jsonl`, distributed under the MIT licence.

Task A booklet PDFs are retrieved from the public Swiss Federal Chancellery collection: [Voting booklets since 1978](https://www.bk.admin.ch/de/sammlung-der-abstimmungsbuechlein-seit-1978).

## 3. Preparing the dataset

Run these commands from `track_2a/`:

```bash
make full
make full splits
```
The preparation script downloads the source JSONL, converts source rows into the project's case format, and downloads the required booklet PDFs.

Each source row normally produces two cases:

- **Task A:** evaluates a claim against evidence in a voting-booklet PDF.
- **Task B:** evaluates a claim against reference text embedded in the case.

Duplicate source rows are removed using the claim text, reference text, and entailment label. The observed dataset contains **1,153 unique rows**, producing **2,306 cases** when both tasks are generated.
The split generator creates the development, validation, and test pools and records their membership in [`docs/splits.json`](../docs/splits.json).

| Setting | Value |
|---|---|
| Split proportions | 40% / 30% / 30% |
| Random seed | `0` |
| Grouping | Voting day |
| Development rows | 458 |
| Validation rows | 372 |
| Test rows | 323 |
All cases associated with the same voting day stay in the same pool. 

## 4. Running the data

### Recommended: dataset directly inside `data/`

Place your files like this:

```text
data/
├── cases.jsonl
└── booklets/
    ├── 2025_11_30_fr.pdf
    └── ...
```

Then run:

```bash
make run
```

The default input is `data/cases.jsonl`, and booklet paths should be relative to the data directory, for example:

```json
{
  "pdf_path": "booklets/2025_11_30_fr.pdf"
}
```
The corresponding PDF must exist at `data/booklets/2025_11_30_fr.pdf`.
### If your dataset is in a subfolder
For example, if your files are inside `data/my_test/`:

```text
data/
└── my_test/
    ├── cases.jsonl
    └── booklets/
```
Run:

```bash
make run DATA=data/my_test
```
The selected data directory is mounted at `/data` inside Docker. Therefore, `booklets/example.pdf` resolves to `/data/booklets/example.pdf` inside the container.
For direct local execution, you can specify the input and output paths explicitly:

```bash
uv run python -m src.cli \
  --input data/my_test/cases.jsonl \
  --output output/my_test-predictions.jsonl
```

### Smoke test

The committed sample contains three source rows expanded into six cases: three Task A cases and three Task B cases. It is intended for pipeline verification, not final benchmark reporting.

Run it with:

```bash
make run DATA=data/sample
```

## 5. Labels and evidence

| Label | Class | Meaning |
|---:|---|---|
| `0` | Entailment | The source supports the claim |
| `1` | Neutral | The source does not determine the claim |
| `2` | Contradiction | The source contradicts the claim |

Task A predictions may include page and text evidence for entailment and contradiction. Neutral Task A predictions have no evidence. Task B predictions do not require PDF citation evidence because the reference text is embedded in the input.

## Related documentation

- [Project README](../README.md) — setup and execution.
- [Technical report](../technical_report.md) — methodology, results, and limitations.
- [Dataset source and licence](https://huggingface.co/datasets/OSTswiss/MNLIoverSwissVotingBooklets)
- [Split manifest](../docs/splits.json)