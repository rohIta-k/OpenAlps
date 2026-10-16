# Design Decisions

This document records the reasoning behind the final Track 2A pipeline. It focuses on the alternatives considered, the trade-offs involved, and why particular approaches were selected or retained.

## 1. PDF Parsing and Source Preparation

**Decision:** Use PyMuPDF to extract page-level text while preserving page numbers and the original text needed for evidence verification.

**Alternatives considered:** Basic text extraction, paragraph-level processing, and more complex layout-aware parsing.

**Rationale:** Page-level extraction provides a practical balance between preserving document structure and keeping preprocessing lightweight. Original extracted text is retained separately from normalized text so that matching can tolerate PDF artifacts without changing the evidence returned to the evaluator.

Complex layout-aware processing was not made a default dependency because it would increase setup and runtime costs without an established improvement sufficient to justify the added complexity.

## 2. Selecting Relevant Pages

**Decision:** Use the voting proposal and document structure to narrow the search space before retrieving evidence.

**Rationale:** Searching an entire booklet introduces irrelevant passages, particularly when a booklet contains multiple voting proposals. Restricting retrieval to the relevant proposal reduces the search space and avoids mixing evidence belonging to different votes.

The selection process uses proposal-title matching and page-level signals, with neighboring-page context and fallback behavior to reduce the risk of excluding relevant evidence.

**Trade-off:** Aggressive filtering can reduce token usage but may remove the page containing the required fact. Page-selection quality therefore needs to be assessed alongside classification performance.

## 3. Chunking Strategy

**Decision:** Use sentence-level units with page metadata for retrieval, while retaining enough surrounding context to reconstruct meaningful passages.

**Alternatives considered:** Fixed-size windows, paragraph-level chunks, and sentence-level retrieval.

**Rationale:** Fixed windows are simple but can split facts, qualifications, or negations across boundaries. Paragraphs preserve more context but may contain irrelevant information. Sentence-level units offer more precise matching for short factual claims and support direct evidence identification.

Neighboring sentences are included when necessary so that retrieved evidence does not lose its original meaning.

## 4. Retrieval Strategy

**Decision:** Combine lexical and semantic retrieval rather than relying exclusively on either method.

**Alternatives considered:** Full-document context, lexical retrieval using BM25, dense multilingual retrieval, and hybrid retrieval.

**Rationale:** BM25 is useful when claims and source passages share exact terms, names, dates, or numbers. Dense multilingual embeddings can identify semantically related passages even when the claim and booklet use different wording or languages.

The hybrid approach combines these complementary signals using Reciprocal Rank Fusion (RRF). This avoids relying entirely on one ranking method and supports the multilingual nature of the task.

The local multilingual embedding model was selected to avoid depending on a separate embedding API at inference time. The added model size and CPU processing cost remain important trade-offs.

## 5. Context Construction

**Decision:** Send selected source passages to Apertus instead of treating retrieval results as an unordered collection of isolated sentences.

**Rationale:** A passage can be relevant lexically but insufficient to establish entailment or contradiction without its surrounding qualifiers, actor, or recommendation. Neighboring context helps preserve these relationships.

The final context is assembled within an input-character budget, with source and page information retained for evidence traceability.


## 6. Classification Prompts and Model Configuration

**Decision:** Use task-specific instructions and structured classification output, with separate configurations for Task A and Task B.

- **Task A:** Classify claims against retrieved voting-booklet context and return supporting evidence.
- **Task B:** Classify claims against the supplied reference text without unnecessary PDF retrieval.

The prompts explicitly distinguish entailment, neutral, and contradiction. They emphasize actor attribution, polarity, numerical details, and the difference between a claim being unsupported and being contradicted.

**Model configuration:** Task A uses Apertus v1.5 70B, while Task B uses Apertus v1.5 8B.

**Rationale:** The tasks provide different amounts and types of context, so they do not require identical processing paths. Explicit classification rules also help prevent the model from treating missing information as proof of contradiction.

Prompt variants, model choices, and other experimental changes should be compared using the corresponding experiment reports rather than assumed to be improvements.

## 7. Evidence Verification

**Decision:** Verify generated evidence against the original source instead of trusting model-produced quotations directly.

**Rationale:** A correct label can still produce invalid evidence if a quotation is paraphrased, fabricated, assigned to the wrong page, or affected by PDF line-break hyphenation.

The verification process tolerates common text-extraction differences while mapping matched evidence back to the original page text. When a required quotation cannot be verified, the pipeline uses its defined fallback behavior rather than returning an unverified quotation as if it were exact.

Task B evidence is also checked against its reference text; page numbers are not applicable to that task.

**Trade-off:** Strict verification improves evidence reliability but can reject legitimate quotations when extraction differs substantially from the source. Evidence quality and classification quality must therefore be considered separately.

## 8. Failure Handling and Output Reliability

**Decision:** Validate model output, handle inference or parsing failures, and maintain the required prediction structure for each input case.

**Rationale:** Model responses may contain malformed JSON, unexpected label formats, or no usable answer. Network errors and missing source files can also interrupt processing.

The pipeline uses parsing and validation, bounded retry behavior where applicable, and a defined neutral fallback for failures that cannot be recovered. Token usage and inference timing are retained where available so that failures do not disappear from performance analysis.

This prioritizes predictable execution and output-contract compliance over allowing one problematic case to terminate an entire run.

## 9. How Final Decisions Were Evaluated

Design choices are not considered improvements solely because they make the architecture more sophisticated.

The evaluation process uses the official `evaluate.py` script from the Hackstarter repository. Experiments are compared using the same evaluation procedure, with attention to classification quality, token usage, inference time, evidence reliability, and failure behavior where those measurements are available.

A change should be retained when its measured benefits justify its additional cost or complexity. Results for individual experiments are documented in the `reports/` folder.

