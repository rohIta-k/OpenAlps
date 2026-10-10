# Setup

## Prerequisites

- Python 3.11
- [`uv`](https://docs.astral.sh/uv/)
- A CSCS API key

Install `uv` if needed, then verify the prerequisites:

```bash
python3.11 --version
uv --version
```

## Install

From the repository root:

```bash
cd track_2a
uv sync
```

`uv sync` creates the virtual environment and installs the dependencies from
the committed `pyproject.toml` and `uv.lock` files.

## Configure the environment

Create a local environment file from the template:

```bash
cp .env.example .env
```

Open `.env` and set `API_KEY` to your CSCS API key. Do not commit `.env`.

To load the variables into the current terminal session:

```bash
set -a
source .env
set +a
```

You can check that the key is present without printing it:

```bash
uv run python -c 'import os; print("API key loaded:", bool(os.getenv("API_KEY")))'
```

## Verify the setup

```bash
uv run ruff check .
uv run pytest
```

The project currently does not provide a completed local run command. Once
the application entry point is available, run it from `track_2a` with the
appropriate `uv run ...` command.