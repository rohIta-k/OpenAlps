# Data used in this project
- **Source**: Hugging Face `OSTswiss/MNLIoverSwissVotingBooklets`, file `v1.1.jsonl`. (MIT licence).
  Booklet PDFs: public federal documents from bk.admin.ch, downloaded via the dataset's `booklet_url`.
- Not stored in this repository (size, and regenerable). To download the full dataset and generate the splits: `make data full splits`.
- **Preparation**: Duplicate rows are removed using the claim text, reference text, and label. (1,153 unique rows from 1.49k rows)cases = one Task A and one Task B case per row.
- **Splits**: by voting day so no day or language version crosses pools; pools 0.4/0.3/0.3, seed 0
  -> dev 458 / val 372 / test 323 rows. The case ids of every split are in `docs/splits.json`.
  Slices run: dev_a 40, dev_b 100, val_a 60, val_b 300; test used once for the final numbers.
- **Experimentation**: Dry runs compared 50/25/25 and 40/30/30. Chose 40/30/30 because validation and test pools are larger, reducing statistical noise by roughly 12% and 7%, respectively. Dev still has 458 rows, enough for the 40–100 cases used during development. With 50/25/25, val_b would be capped at 289 instead of the target 300.
- **Testing with your own data:** Provide a `cases.jsonl` file. Each line is one case and must follow one of these formats:
  **Task A:** claim evaluated against a booklet PDF.
  ```json
  {"id":"example-A","vote":"Example vote","claim":{"text":"Example claim","language":"en"},"booklet":{"path":"booklets/2025_11_30_de.pdf","language":"de"}}
  ```
  **Task B:** claim evaluated against a reference text.
  ```json
  {"id":"example-B","vote":"Example vote","claim":{"text":"Example claim","language":"en"},"reference":{"text":"Example reference text","language":"de"}}
  ```
  For Task A, place the corresponding PDFs in a `booklets/` folder. Name them
  `YYYY_MM_DD_<language>.pdf`, for example `2025_11_30_de.pdf`.
  The main entry point uses `data/cases.jsonl` by default, so run it with the
  default input when your cases are stored there. If you store the cases in a
  subfolder, pass that file explicitly with `--input`. For example, for
  `data/my_test/cases.jsonl`, use `--input data/my_test/cases.jsonl`.
- **`data/sample/`**: 3 dataset rows (3 Task A + 3 Task B cases) with their PDFs, the first rows of the dev split,
  used by `make run`. The graded evaluation uses the organisers' private set.