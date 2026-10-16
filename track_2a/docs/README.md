# Documentation
This directory contains the technical documentation for Track 2A, covering setup, configuration, architecture, pipeline implementation, experiments, evaluation, design decisions, testing, and troubleshooting.

## Quick navigation

### Getting started
- [Setup and execution](setup.md) — prerequisites, dependency installation, model preparation, input data, and running locally or with Docker.
- [Configuration](configuration.md) — environment variables, API settings, model paths, data mounts, and mock/offline behaviour.
### System design and implementation
- [Architecture](architecture.md) — system components, responsibilities, interfaces, and end-to-end data flow.
- [Pipeline](pipeline.md) — step-by-step execution from input cases to predictions.
- [Retrieval](retrieval.md) — PDF processing, text extraction, chunking, embeddings, and evidence retrieval.
- [Classification](classification.md) — Apertus inference, prompts, label mapping, output parsing, and evidence requirements.
### Evaluation
- [Dataset documentation](../data/README.md) — dataset sources, input format, data layout, preparation, and split details.
- [Split manifest](splits.json) — recorded development, validation, and test membership.
### Engineering and maintenance
- [Design decisions](Decisions.md) — alternatives considered, selected approaches, trade-offs, and rationale.

The [project README](../README.md) provides the project overview and entry point. The [technical report](../technical_report.md) presents the consolidated account of the system and its findings, with links to the relevant documentation in this directory.