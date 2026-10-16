# Hack Apertus — Track 2A (OST)

**Multilingual Natural Language Inference over Swiss Official Voting Booklets**

A document-grounded claim verification system that uses multilingual evidence retrieval and Apertus v1.5 models to classify claims against official Swiss voting documents.

## 🎯 Project Overview

Given a natural-language claim and its associated Swiss voting booklet, the system determines whether the booklet supports, contradicts, or provides insufficient information about the claim.

| Label | Relationship | Meaning |
|---|---|---|
| **0** | Entailment | The booklet supports the claim. |
| **1** | Neutral | The booklet does not provide enough information to determine whether the claim is supported or contradicted. |
| **2** | Contradiction | The booklet contradicts the claim. |

The challenge goes beyond simple text matching. Relevant evidence may be scattered across lengthy PDFs, expressed through qualifications or negations, or written in a different language from the claim.

**The solution combines multilingual retrieval, document-grounded reasoning, and evidence validation** to produce structured predictions tied to the source document.

## ⚙️ Solution at a Glance

The system follows a four-stage pipeline:

1. **Document Processing**
   - Extract and clean text from official voting booklet PDFs.
   - Split the text into sentence-level evidence units while preserving source-page information.

2. **Multilingual Evidence Retrieval**
   - Combine lexical matching with embeddings from `paraphrase-multilingual-MiniLM-L12-v2`.
   - Retrieve relevant passages across German, French, Italian, and cross-lingual claim–document pairs.

3. **Claim Classification**
   - Use Apertus v1.5 models to classify claims against the retrieved evidence.
   - Produce structured predictions with supporting evidence where applicable.

4. **Evidence Validation & Output**
   - Check generated evidence against the extracted booklet text.
   - Write structured JSONL predictions with classification and source information.

## 🗂️ Repository Structure

```text
.
├── Makefile                     # Root command entry point
├── track_2a/
│   ├── README.md                # Detailed setup and usage
│   ├── technical_report.md      # Architecture, evaluation, limitations
│   ├── Makefile                 # Track-specific commands
│   ├── Dockerfile               # Containerized execution
│   ├── src/                     # Application source code
│   ├── scripts/                 # Model preparation and utilities
│   ├── models/                  # Local embedding model
│   └── data/                    # Input datasets and sample data
```

The root `Makefile` forwards commands to `track_2a/`, allowing the project to be run from the repository root while preserving the required track directory structure.

## 🚀 Getting Started

### Requirements

- Docker installed and running.
- An OpenAI-compatible Apertus v1.5 inference endpoint and valid API credentials for real inference.
- The local multilingual embedding model, prepared using the instructions in [`track_2a/README.md`](track_2a/README.md).

### Configure the environment

From the repository root:

```bash
cp track_2a/.env.example track_2a/.env
```

Configure the inference endpoint and API key in `track_2a/.env` using `BASE_URL` and `API_KEY`. The aliases `LLM_BASE_URL` and `LLM_API_KEY` are also accepted.

### Run the project

```bash
make run
```

The root Makefile forwards the command to `track_2a/`. Docker builds the image and runs inference on the configured input dataset.

To run against the sample dataset explicitly:

```bash
make -C track_2a run DATA=data/sample
```

For model preparation, input configuration, environment variables, and troubleshooting, see [`track_2a/README.md`](track_2a/README.md).

## 📄 Output

Predictions are written to:

```text
track_2a/output/predictions.jsonl
```

Each line represents a structured JSONL prediction containing the claim classification and, when available, grounded evidence passages and source-page information.

## 📚 Further Documentation

- [Track 2A README](track_2a/README.md) — setup, execution, configuration, and troubleshooting.
- [Technical Report](track_2a/technical_report.md) — architecture, model choices, evaluation, limitations, and design decisions.
- [OST Challenge Dataset](https://huggingface.co/datasets/OSTswiss/MNLIoverSwissVotingBooklets) — benchmark claim–document pairs and label definitions.

## 📜 License

Hack Apertus projects are open-sourced. Refer to the [Hack Apertus Terms & Conditions](https://hackapertus.ch/terms-and-conditions) for the applicable licensing requirements.
