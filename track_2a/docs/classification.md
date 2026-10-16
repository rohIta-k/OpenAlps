# Classification and evidence

## Apertus interface

[`LLMClient`](../src/llm_client.py) uses the OpenAI-compatible
`chat.completions.create` interface. It sends `temperature=0`, the selected
maximum token count, a task-specific model identifier, and a strict JSON Schema
response format:

- Task A: `swiss-ai/Apertus-v1.5-70B`, with structured evidence objects.
- Task B: `swiss-ai/Apertus-v1.5-8B`, with `"evidence": null`.

The endpoint is configured by `BASE_URL` (default
`https://api.inference.cscs.ch/v1`) and authenticated with `API_KEY` or its
documented alias. `MOCK_LLM=1` bypasses the API and returns intentionally fake
neutral responses for CI/container checks only.

## Prompt structure and labels

[`src/prompts.py`](../src/prompts.py) supplies a shared decision procedure.
The model must distinguish:

- `entailment`: the source supports the claim, including its actor, action,
  polarity, quantities, dates, conditions, and scope;
- `contradiction`: the source directly conflicts with an essential claim
  detail; and
- `neutral`: the source is silent, incomplete, ambiguous, unrelated, or does
  not establish a required detail.

The numeric mapping is applied after parsing:

```text
0 -> entailment
1 -> neutral
2 -> contradiction
```

The prompt explicitly warns against treating missing support as contradiction,
mixing different votes or actors, confusing existing law with a proposal, and
using outside knowledge.

## Task-specific prompt inputs

Task A receives:

```text
VOTE: <vote name>

BOOKLET:
[[PAGE 4]]
[S00021 p.4] <retrieved sentence>
[S00022 p.4] <neighboring sentence>

CLAIM (language: <language>): <claim>
```

The system prompt says that the passages are partial excerpts, requires
verbatim evidence from supplied sentences, and requires the sentence's
1-based PDF page. Sentence IDs and page markers are metadata, not quote text.

Task B receives the vote, the complete embedded `SOURCE` passage, and the claim.
It uses the same semantic decision rules but explicitly forbids evidence
generation:

```json
{"label": "entailment|neutral|contradiction", "evidence": null}
```

## Parsing and malformed responses

[`parse_output_detailed`](../src/parsing.py) requires a JSON object with a
valid label and an `evidence` field. It rejects invalid JSON, non-object
responses, unknown labels, non-list/non-null evidence, invalid page numbers,
empty or oversized quotes, more than five items, and non-neutral labels with no
evidence. Evidence returned for a neutral label is discarded with a warning.
`null` evidence is normalized to an empty list for downstream consistency.

The pipeline gives a malformed response one retry. It appends a correction
instruction naming the validation failure and asks for a complete schema-valid
JSON object. If that request fails or remains malformed,
[`_fallback`](../src/pipeline.py) emits label `1`, empty evidence, and the
available token/time metrics. The same neutral fallback covers unexpected
per-case errors such as a missing PDF.

The client itself retries transient connection, timeout, rate-limit, and
selected server errors with bounded exponential backoff. It does not retry
ordinary non-retryable client errors indefinitely.

## Evidence rules

### Task A

For entailment or contradiction, the model should return one to four
`{"page": integer, "text": string}` items copied from the supplied excerpts.
Neutral must return an empty array. After parsing, `build_evidence_a` verifies
the quote against the original PDF pages, returns the PDF's own text span, and
keeps the page number 1-based. It deduplicates matches and caps final evidence
at five items.

If no quote matches but a non-neutral label requires evidence, the code uses a
page hint or word-overlap page and finally the first non-empty page. This is a
contract-preserving fallback, not proof that the model's quotation was correct.

### Task B

The model must return `evidence: null`; the final contract uses `evidence: []`.
No citation mapping is performed because the reference text is already part of
the input and has no PDF page requirement.

## Difficult claims and error patterns

The prompt and retrieval design specifically target claims where surface
similarity is misleading:

| Claim pattern | Correct distinction |
|---|---|
| “The committee recommends rejecting the proposal.” vs. a source saying the proposal is unsuitable | Likely entailment if the source expresses the same stance; do not reverse the direction. |
| A claim attributes Parliament's position to the Federal Council | Neutral or contradiction depending on the source's explicit actor; shared topic is not enough. |
| “The measure reduces the tax by 20%” vs. a source giving a different percentage | Contradiction when the source clearly gives the incompatible figure. |
| “The proposal was accepted” vs. a booklet describing what would happen if accepted | Neutral: hypothetical consequences do not establish an acceptance result. |
| A claim adds an unsupported cause, date, scope, or certainty to an otherwise related statement | Neutral unless the source directly conflicts with that added detail. |
| A negated claim and a source with the opposite polarity | Entailment or contradiction must follow the actual polarity, not keyword overlap. |

Common operational error patterns are missing/invalid JSON, unsupported model
evidence, wrong page hints, retrieval of a different proposal in the same
booklet, and overconfident contradiction when the source is merely silent.
`validate_output.py` catches structural violations, while evidence verification
and the evaluation script reveal weak citations and label errors.
