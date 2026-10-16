# Setup and execution
This guide explains how to run Track 2A with your own input data, either locally or using Docker.
Commands can be run from the repository root or from `track_2a/`. The root Makefile forwards supported targets to the track directory.
```bash
# From the repository root
make run
# Or from the track directory
cd track_2a
make run
```
## 1. Prerequisites
- Python 3.11
- [uv](https://docs.astral.sh/uv/)
- Docker with Buildx support and a running Docker daemon
- GNU Make
- An Apertus-compatible API key for real inference
The Docker image targets `linux/amd64`. On Apple Silicon, Docker Desktop must support amd64 emulation.
## 2. Install dependencies
From `track_2a/`, run:
```bash
uv sync
```
Alternatively, use the Makefile:
```bash
make setup
```
To check code style, run:
```bash
make lint
```
## 3. Configure API access
For real inference, create a local environment file if one does not already exist:

```bash
cp .env.example .env
```
Add your API key and any required endpoint or model settings to `.env`. Keep this file private and never commit real credentials.
Mock mode does not require API credentials. See [configuration.md](configuration.md) for supported variables and defaults.
## 4. Prepare the embedding model
The retrieval pipeline uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
If the model files are not already available under `models/`, download them from `track_2a/`:
```bash
uv run python scripts/download_model.py
```
If the Dockerfile copies the model into the image, prepare the model before building or running the Docker pipeline. The Apertus model is accessed through the configured API; its weights are not downloaded by this project.

## 5. Provide your input data

**Recommended:** place your input directly inside `track_2a/data/`.

```text
data/
├── cases.jsonl
└── booklets/
    ├── example.pdf
    └── ...
```

- `cases.jsonl` contains the cases to evaluate.
- `booklets/` contains the PDFs referenced by Task A cases.
- Task B cases contain their reference text in the input record.
Use paths relative to the selected data directory, such as `booklets/example.pdf`, rather than absolute paths from your computer.
For the required JSONL fields and complete input format, see the [dataset documentation](../data/README.md).

### If your input is in a subfolder
For example:

```text
data/
└── my_test/
    ├── cases.jsonl
    └── booklets/
        └── example.pdf
```
Specify the subfolder with `DATA` when running a command:
```bash
make run DATA=data/my_test
```
The selected directory is mounted at `/data` inside Docker. Case paths must therefore resolve relative to that mounted directory.
## 6. Run the pipeline
### Docker with real inference
Using the default `data/` directory:

```bash
make run
```
Using the committed smoke-test sample:
```bash
make run DATA=data/sample
```
Using a custom subfolder:

```bash
make run DATA=data/my_test
```
The command builds and runs the Docker image, mounts the selected input directory read-only at `/data`, and mounts the output directory at `/output`.
Predictions are written to:

```text
track_2a/output/predictions.jsonl
```
Real inference requires a valid API key and access to the configured endpoint.
### Docker mock mode
To verify the container and output pipeline without making real inference calls:
```bash
make run-mock DATA=data/sample
```
Mock predictions are for pipeline testing only and must not be used as benchmark results.
### Local execution
To run without Docker, use:
```bash
make run-local
```
For a custom input directory:
```bash
make run-local DATA=data/my_test
```
The local command uses the selected input directory and writes predictions to the configured output path. Local real inference also requires the API credentials and runtime configuration to be available to the process.

## 7. Verify the output
After the run, check:

```text
output/predictions.jsonl
```
Confirm that the file exists, predictions follow the expected output schema, and the results correspond to the intended input cases. Review the logs for invalid cases, missing PDFs, or inference errors.

If something fails, consult [configuration.md](configuration.md) and [troubleshooting.md](troubleshooting.md).