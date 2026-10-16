# PDF extraction and retrieval

Task A retrieval is implemented in
[`src/pdf_loader.py`](../src/pdf_loader.py),
[`src/page_scoring.py`](../src/page_scoring.py),
[`src/sentence_splitter.py`](../src/sentence_splitter.py),
[`src/retrieval.py`](../src/retrieval.py), and
[`src/chunking.py`](../src/chunking.py).

## PDF loading and cleaning

[`load_pages`](../src/pdf_loader.py) opens a booklet with PyMuPDF and returns
one string per physical page. Extraction uses `page.get_text("blocks",
sort=True)` and orders blocks top-to-bottom, then left-to-right. This keeps
headings and columns more stable than treating the complete document as one
unstructured string.

The `_clean` helper:

- applies Unicode NFKC normalization;
- removes soft hyphens and converts non-breaking spaces;
- joins words split by a line-break hyphen;
- normalizes curly quotation marks;
- collapses horizontal whitespace; and
- joins wrapped lines inside paragraphs while preserving paragraph breaks.

Page arrays are cached, and page numbers are always converted to human-facing
1-based numbers when sentence records or evidence are created. The original
page text is retained for evidence verification.

## Page selection and sections

Before sentence retrieval, [`select_relevant_pages`](../src/page_scoring.py)
scores every page against the case's vote title. Exact normalized title
matches score `100`; otherwise distinctive title words are weighted by
within-booklet IDF. Pages at or above `15` start relevant blocks, neighboring
pages at or above `5` are expanded, and one context page is added on each side.
The selected set is capped at `15` pages. If no page reaches the threshold, the
full booklet is retained.

Section labels are optional metadata. The system first detects multilingual
contents pages in the first 12 physical pages, maps printed page numbers to
physical pages, and recognizes headings such as “In Kürze”, “En bref”, and “In
breve”. If that fails, recognized PDF bookmarks are used.

## Sentence segmentation and chunks

[`build_sentence_units`](../src/sentence_splitter.py) splits each page with
sentence-ending punctuation while protecting common abbreviations such as
`Dr.`, `Art.`, `z. B.`, `p. ex.`, and their multilingual equivalents. Each
record has a stable ID, 1-based page, optional section, source text, and
position:

```python
{
    "id": "S00001",
    "page": 3,
    "section": "Erste Vorlage — In Kürze",
    "text": "Sentence copied from the cleaned PDF page.",
    "position": 0,
}
```

[`pack_top_k_context`](../src/chunking.py) takes ranked sentences and expands
each by one neighboring sentence (`radius=1`) on the same page, without
crossing source-position gaps. Selected sentences are deduplicated by ID,
returned in original source order, and rendered with `[[PAGE n]]` and
`[Sxxxxx p.n]` markers. It accepts as much context as fits the
`MAX_INPUT_CHARS` budget, whose default is `600000`.

## Lexical and semantic retrieval

[`HybridRetriever`](../src/retrieval.py) uses two rankings:

1. **Lexical:** a repository implementation of BM25 with `k1=1.5` and
   `b=0.75`. Tokenization retains numbers, dates, punctuation-separated
   numeric forms, and multilingual negation terms.
2. **Semantic:** `paraphrase-multilingual-MiniLM-L12-v2`, loaded from the local
   model directory with `local_files_only=True` when available. Document and
   query embeddings are encoded with `normalize_embeddings=True`, so vector
   scores are cosine-like dot products.

The embedding model is loaded lazily on the first retrieval request and
document embeddings are cached for that retriever. If a model path is not a
directory during local execution, the retriever downloads and saves the
configured multilingual model; Docker prevents this fallback with
`HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`.

## Merging, ranking, and limits

Each ranking is converted to reciprocal-rank contributions with
`RRF_K=60`. The default lexical and semantic weights are both `1.0`. Results
are sorted by descending fused score, then original sentence order, and the
top `30` candidates are returned.

The pipeline sends only the first `15` ranked candidates to context packing.
Neighbor expansion can add adjacent sentences, but the set of sentence IDs is
deduplicated before rendering. Context that would exceed the character budget
is skipped and `truncated` is recorded; the pipeline logs a warning.

## Evidence mapping

The model receives sentence IDs and page labels but must quote only source text.
After classification, [`PageIndex`](../src/evidence.py) squashes quotes and
page text to lowercase alphanumeric characters, making verification tolerant of
case, whitespace, punctuation, and PDF hyphenation differences. Matching
quotes are returned as spans from the original page text, with the hinted page
checked first. At most five evidence items are emitted, with a roughly 4,500
character per-item limit.

If a required non-neutral quote cannot be found, the evidence builder tries the
model's page hint, a best-overlap page, and finally the first non-empty page.
This preserves the output contract but may be weak evidence, so such fallbacks
should be inspected during evaluation.

## Known failure modes and improvements

The implementation has several predictable retrieval risks:

- OCR errors, unusual reading order, multi-column layouts, tables, and
  scanned/image-only PDFs can produce incomplete or misordered text.
- Sentence splitting is punctuation-based and may mishandle headings,
  abbreviations not in its list, and language-specific typography.
- Vote-title page scoring can miss relevant pages when the title is abbreviated,
  translated differently, or absent from the body; full-booklet fallback is
  more expensive and noisier.
- BM25 can over-rank shared names, numbers, or vote terminology, while
  embeddings can blur negation, actors, dates, and similar proposals.
- A small page cap and character budget can omit a decisive passage.
- Exact quote verification rejects paraphrases, even when the classification
  itself is correct.

Potential improvements include layout-aware extraction or OCR, language-aware
sentence segmentation, cross-encoder reranking, explicit negation/number
features, query expansion from vote metadata, adaptive page budgets, and
logging retrieval recall against gold evidence before changing thresholds.
