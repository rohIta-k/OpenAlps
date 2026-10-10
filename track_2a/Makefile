SHELL := /bin/bash
IMAGE        ?= track2a
# Default: use data/cases.jsonl for judge-provided data.
# To test with the sample dataset, run: make run DATA=data/sample
DATA         ?= data/sample
ENVFILE      ?= .env
PY           ?= uv run python
WORKERS      ?= 2
POOLS        ?= 0.4,0.3,0.3
SEED         ?= 0
PREDICTIONS  ?= output/predictions.jsonl
NAME         ?= run
NOTES        ?=

.PHONY: help setup lint run run-mock run-local validate eval log stats \
        data full splits clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "%-12s %s\n", $$1, $$2}'

setup:
	uv sync

lint: 
	uv run ruff check . --fix

test: 
	uv run python -m pytest -q

run: ## Build Docker image and run real model inference on DATA
	@test -f $(ENVFILE) || { echo "Missing $(ENVFILE). Run: cp .env.example .env"; exit 1; }
	@test -f $(DATA)/cases.jsonl || { echo "Missing $(DATA)/cases.jsonl"; exit 1; }
	docker build --platform linux/amd64 -t $(IMAGE) .
	mkdir -p output
	docker run --rm --platform linux/amd64 --env-file $(ENVFILE) \
	  -v "$(CURDIR)/$(DATA):/data:ro" \
	  -v "$(CURDIR)/output:/output" \
	  $(IMAGE) --input /data/cases.jsonl --output /output/predictions.jsonl

run-mock: ## Run Docker with fake model responses; no API calls or network
	@test -f $(DATA)/cases.jsonl || { echo "Missing $(DATA)/cases.jsonl"; exit 1; }
	docker build --platform linux/amd64 -t $(IMAGE) .
	mkdir -p output
	docker run --rm --platform linux/amd64 --network none --read-only \
	  --tmpfs /tmp -e MOCK_LLM=1 \
	  -v "$(CURDIR)/$(DATA):/data:ro" \
	  -v "$(CURDIR)/output:/output" \
	  $(IMAGE) --input /data/cases.jsonl --output /output/predictions.jsonl

run-local: ## Run inference locally without Docker on DATA
	@test -f $(DATA)/cases.jsonl || { echo "Missing $(DATA)/cases.jsonl"; exit 1; }
	mkdir -p output
	DATA_DIR=$(DATA) DEBUG_DIR=output/debug \
	  $(PY) -m src.cli --input $(DATA)/cases.jsonl \
	  --output $(PREDICTIONS)

validate: ## Validate predictions against the output contract
	$(PY) scripts/validate_output.py \
	  --cases $(DATA)/cases.jsonl \
	  --predictions $(PREDICTIONS)

eval: ## Evaluate predictions against labels for DATA
	$(PY) scripts/quick_eval.py \
	  --predictions $(PREDICTIONS) \
	  --expected $(DATA)/expected-labels.jsonl \
	  --cases $(DATA)/cases.jsonl

log: ## Log an experiment (NAME=... NOTES=...)
	$(PY) scripts/log_run.py \
	  --name "$(NAME)" --notes "$(NOTES)" \
	  --predictions $(PREDICTIONS) \
	  --expected $(DATA)/expected-labels.jsonl \
	  --cases $(DATA)/cases.jsonl

stats: ## Summarize tokens and latency for PREDICTIONS
	$(PY) scripts/summarize_metrics.py --predictions $(PREDICTIONS)

full:  ## Prepare all cases and download all booklet PDFs
	$(PY) scripts/prepare_cases.py --output-dir data/full --download-booklets

splits:  ## Generate frozen dev/val/test splits and docs/splits.json
	$(PY) scripts/make_splits.py --src data/full \
	  --pools $(POOLS) --seed $(SEED)

clean: 
	rm -rf output .pytest_cache .ruff_cache
