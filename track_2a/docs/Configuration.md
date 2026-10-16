# Configuration reference
Track 2A loads runtime settings from environment variables and `.env` files. Environment variables take precedence over values loaded from `.env`. The implementation is defined in [`src/config.py`](../src/config.py) and [`src/llm_client.py`](../src/llm_client.py), with additional runtime defaults in [`Dockerfile`](../Dockerfile).

## 1. Runtime environment variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `BASE_URL` | `https://api.inference.cscs.ch/v1` | For real inference | OpenAI-compatible Apertus API endpoint. |
| `LLM_BASE_URL` | None | No | Alias for `BASE_URL`, used when `BASE_URL` is unset. |
| `API_KEY` | None | For real inference | API credential. |
| `LLM_API_KEY` | None | No | Alias for `API_KEY`, used when `API_KEY` is unset. |
| `MAX_OUTPUT_TOKENS` | `500` | No | Maximum completion tokens for Task A. |
| `MAX_INPUT_CHARS` | `600000` | No | Character budget for packed Task A retrieval context. |
| `TIMEOUT_S` | `500` | No | Inference HTTP timeout in seconds. |
| `DATA_DIR` | `/data` | No | Base directory used to resolve booklet paths. |
| `MOCK_LLM` | `0` | No | Set to `1` to return deterministic fake neutral predictions without API calls. |
Defaults should be interpreted in the context of the execution environment: the Dockerfile can override Python defaults.
If both variables in an alias pair are set, the primary variable wins: `BASE_URL` over `LLM_BASE_URL`, and `API_KEY` over `LLM_API_KEY`.

## 2. Apertus API and model selection
The pipeline uses the following model identifiers, selected by task in [`src/llm_client.py`](../src/llm_client.py):
| Task | Model identifier | Purpose |
|---|---|---|
| Task A | `swiss-ai/Apertus-v1.5-70B` | Classifies claims using retrieved voting-booklet evidence. |
| Task B | `swiss-ai/Apertus-v1.5-8B` | Classifies claims using the reference text embedded in each case. |
Both models are accessed through the configured OpenAI-compatible endpoint. Their weights are not downloaded by this project.
For real inference, configure the endpoint and API key in `.env`:
```dotenv
BASE_URL=https://api.inference.cscs.ch/v1
API_KEY=<your-secret-key>
```
The API connectivity smoke test in [`scripts/smoke_test_api.py`](../scripts/smoke_test_api.py) uses `swiss-ai/Apertus-v1.5-8B` by default. This setting is for the smoke test only; the main pipeline selects its models separately for Task A and Task B.

## 3. Embedding model and offline behaviour
The retriever uses the multilingual embedding model:
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
Expected local model directory:
```text
models/paraphrase-multilingual-MiniLM-L12-v2/
```
The Dockerfile sets:
```text
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```
These settings prevent Hugging Face downloads inside the container. The embedding model must be available locally before the image is built if the Dockerfile copies it into the image.

## 4. Input, output, and Makefile settings
The CLI accepts explicit input and output paths:
```bash
uv run python -m src.cli \
  --input data/cases.jsonl \
  --output output/predictions.jsonl
```
The Makefile exposes the following variables:
| Variable | Default | Purpose |
|---|---|---|
| `DATA` | `data` | Host directory containing `cases.jsonl` and referenced `booklets/`. |
| `ENVFILE` | `.env` | Environment file used for real Docker inference. |
| `IMAGE` | `track2a` | Docker image tag. |
| `PY` | `uv run python` | Local Python command. |
| `PREDICTIONS` | `output/predictions.jsonl` | Local prediction output path. |
| `POOLS` | `0.4,0.3,0.3` | Development, validation, and test split proportions. |
| `SEED` | `0` | Split-generation random seed. |
`POOLS` and `SEED` apply to dataset split generation, not inference.
### Docker path mapping
For example, with:

```bash
make run DATA=data/sample
```
the selected host directory is mounted read-only at `/data` inside the container, and the project's output directory is mounted at `/output`.

| Host path | Container path |
|---|---|
| `data/sample/cases.jsonl` | `/data/cases.jsonl` |
| `data/sample/booklets/example.pdf` | `/data/booklets/example.pdf` |
| `output/predictions.jsonl` | `/output/predictions.jsonl` |

Consequently, case records should use paths relative to the selected data directory, such as `booklets/example.pdf`, rather than host-specific absolute paths.
The actual defaults and mount arguments are defined in the Makefile and Dockerfile.
## 5. Execution modes
| Mode | API key | Network access | Intended use |
|---|---|---|---|
| Local real inference | Required | Requires access to the configured API endpoint | Local development and inference. |
| Docker real inference | Required through `ENVFILE` | Requires API endpoint access at runtime | Containerized inference and judge-style execution. |
| Docker mock mode | Not required | Disabled by the mock Docker command | Container and output-contract smoke tests. |
### Mock mode

Setting `MOCK_LLM=1` makes the pipeline return fake neutral predictions without calling the inference API. The mock Docker command also uses `--network none`, `--read-only`, and a temporary `/tmp` filesystem.