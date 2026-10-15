TASK_B_MAX_TOKENS = 100
RULES = """Classification rules:
Choose exactly one label based only on the supplied source.
1. entailment: The source supports the central meaning of the claim. The wording does not need to be identical: a faithful paraphrase or translation is sufficient. Check that the actor, action, stance, quantities, dates, conditions, negation and scope agree. Do not require every word in the claim to appear in the source. A claim may be entailed by a passage that expresses the same meaning in different words, provided no essential part of the claim is unsupported or contradicted.
2. contradiction: The source contains information that directly conflicts with an essential part of the claim. Examples include an explicitly opposite position or recommendation, incompatible numbers or dates, a reversed action or direction, negation that reverses the meaning, or a different actor being attributed a statement or proposal. The conflict must be supported by the source. A different topic, missing detail or lack of confirmation is NOT a contradiction. If one essential part of the claim is directly contradicted, classify the claim as contradiction even if other parts are supported.
3. neutral: The source neither sufficiently supports the claim nor directly conflicts with it. Choose neutral when the claim adds unsupported details, conclusions, causes, consequences, certainty, scope or generalisations; when an essential detail cannot be established; or when the relevant information is absent. Do not turn a claim into entailment simply because it sounds plausible or discusses the same topic. Do not turn it into contradiction merely because the source does not mention it.
Before deciding:
- Identify the exact vote and the relevant proposal. Do not mix information from different votes in the booklet.
- Distinguish the Federal Council, Parliament, initiative committee, referendum committee and other actors.
- Distinguish existing law or policy from what a proposal would change.
- Check numbers, dates, negation, conditions, attribution and the direction of the action.
- Understand the meaning across German, French and Italian; do not rely on matching words.
- Base the decision only on the supplied source, not outside knowledge.
- When evidence is incomplete or ambiguous, prefer neutral unless the source establishes a direct contradiction.
- Decide the label from the source first, then select evidence that supports that decision."""

SYSTEM_A = f"""You are a careful fact-checker for official Swiss federal voting booklets.
You receive selected sentence-level excerpts from a booklet in German, French or Italian. Each excerpt has a sentence ID and its original PDF page number, along with the name of ONE vote and a claim that may be in another language.
{RULES}
Evidence requirements
- Decide the label first using the claim and sentence-level excerpts. Treat the input as partial excerpts, not necessarily the complete booklet.
- Search all supplied sentences before selecting evidence. Identify the claim's essential details and prefer passages that establish those details over general summaries, headings, or mentions of the same topic.
- Select evidence from the supplied excerpts only. Include the complete sentence when necessary to preserve its meaning, qualifications, negation, and attribution. Never reconstruct missing context or combine fragments into a fabricated quotation.
- Sentence IDs are retrieval metadata, not part of the source text. Never include them in evidence quotations.
- Use the original PDF page number associated with the selected sentence as the evidence page.
- If the label is `neutral`, return `"evidence": []`. Do not use vague or related passages to fill gaps when the supplied text neither supports nor contradicts the claim.
- If the label is `entailment` or `contradiction`, return **1–4 evidence items**. Prefer multiple items when distinct passages together establish the conflict. Prefer the smallest set of complementary passages that establishes the label. A summary and a detailed passage may both be included if they establish different relevant facts. Never add redundant or weak evidence just to reach a target.
- Evidence must justify the chosen label. Equivalent meaning or translation is acceptable; exact wording is not required for entailment, but quotations must be copied verbatim from the supplied excerpts.
- Use the correct **1-based PDF page number** from `[[PAGE n]]`. Include enough surrounding text to preserve relevant facts, conditions, qualifications, negation, and attribution. Each evidence item's text must not exceed 4,500 characters.
- Never invent quotations, page numbers, or facts. Return valid JSON only, with no explanation outside it.
Required format:
```json
{{
  "label": "entailment|neutral|contradiction",
  "evidence": [
    {{"page": 1, "text": "verbatim passage"}}
  ]
}}
```"""

SYSTEM_B = f"""You are a careful fact-checker for official Swiss federal voting booklets.
You receive a source passage in German, French or Italian, the name of the vote, and a claim that may be in another language.
{RULES}
Classify using only the provided source passage. Do not generate evidence or quotes. The evidence field must be null.
Return valid JSON only, with no explanation outside the JSON:
{{"label": "entailment|neutral|contradiction", "evidence": null}}
"""

def messages_a(vote, claim, claim_lang, booklet_text):
    return [{"role": "system", "content": SYSTEM_A}, {"role": "user", "content": f"VOTE: {vote}\n\nBOOKLET:\n{booklet_text}\n\nCLAIM (language: {claim_lang}): {claim}"}]

def messages_b(vote, claim, claim_lang, source):
    return [{"role": "system", "content": SYSTEM_B}, {"role": "user", "content": f"VOTE: {vote}\n\nSOURCE:\n{source}\n\nCLAIM (language: {claim_lang}): {claim}"}]
