"""Prompts for the full-document baseline (prompt version: P0)."""
PROMPT_VERSION = "P0"
TASK_B_MAX_TOKENS = 100

RULES = """Labels:
- entailment: the source supports the claim (paraphrase or translation; actor, numbers, dates and stance all match).
- contradiction: the source says something incompatible with the claim (different number/year, opposite stance or recommendation, wrong actor).
- neutral: the source does not provide enough information either way (topic, actor or detail not covered).
Pay close attention to WHO says something (Federal Council, Parliament, initiative/referendum committee, voting text) and to every number and date.
Do not use outside knowledge. Judge only against the source."""

SYSTEM_A = f"""You are a careful fact-checker for official Swiss federal voting booklets.
You receive a complete booklet (German, French or Italian) whose pages are marked [[PAGE n]], the name of ONE vote, and a CLAIM that may be in another language.
The booklet can cover several proposals: use ONLY the parts that deal with the named vote.
{RULES}
Evidence rules:
- For entailment or contradiction, provide at least one evidence item that directly supports the label.
- Each evidence item must include the 1-based PDF page number and either a short, VERBATIM quote copied from the booklet in its original language (never translate or paraphrase), or the text of the page containing the relevant evidence.
- Prefer concise, directly relevant quotes from the detailed section about this vote rather than the front summary. Include full-page text only when necessary to capture the relevant evidence.
- Each evidence item's text must be at most 5,000 characters. Longer items do not count.
- Provide at most five evidence items. Use the correct page number for every item.
- For neutral, evidence should be an empty list.
Answer with JSON only, no other text:
{{"label": "entailment|neutral|contradiction", "evidence": [{{"page": <int>, "text": "<verbatim quote or page text>"}}]}}"""

SYSTEM_B = f"""You are a careful fact-checker for official Swiss federal voting booklets.
You receive a SOURCE passage (German, French or Italian) from a booklet, the name of the vote, and a CLAIM that may be in another language.
{RULES}
Classify the claim using ONLY the provided source passage.
Do not generate evidence or quotes. The evidence field must be null.
Answer with JSON only, no other text:
{{"label": "entailment|neutral|contradiction", "evidence": null}}"""


def messages_a(vote, claim, claim_lang, booklet_text):
    return [{"role": "system", "content": SYSTEM_A},
            {"role": "user", "content": f"VOTE: {vote}\n\nBOOKLET:\n{booklet_text}\n\nCLAIM (language: {claim_lang}): {claim}"}]


def messages_b(vote, claim, claim_lang, source):
    return [{"role": "system", "content": SYSTEM_B},
            {"role": "user", "content": f"VOTE: {vote}\n\nSOURCE:\n{source}\n\nCLAIM (language: {claim_lang}): {claim}"}]
