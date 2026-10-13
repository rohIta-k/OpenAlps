TASK_B_MAX_TOKENS = 100
RULES = """Classification rules:
Choose exactly one label based only on the supplied source.
1. entailment: The source supports the central meaning of the claim. The wording does not need to be identical: a faithful paraphrase or translation is sufficient. Check that the actor, action, stance, quantities, dates, conditions, negation and scope agree. Do not require every word in the claim to appear in the source. A claim may be entailed by a passage that expresses the same meaning in different words, provided no essential part of the claim is unsupported or contradicted.
2. contradiction: The source contains information that directly conflicts with an essential part of the claim. Examples include an explicitly opposite position or recommendation, incompatible numbers or dates, a reversed action or direction, negation that reverses the meaning, or a different actor being attributed a statement or proposal. The conflict must be supported by the source. A different topic, missing detail or lack of confirmation is NOT a contradiction. If one essential part of the claim is directly contradicted, classify the claim as contradiction even if other parts are supported.
3. neutral: The source neither sufficiently supports the claim nor directly conflicts with it. Choose neutral when the claim adds unsupported details, conclusions, causes, consequences, certainty, scope or generalisations; when an essential detail cannot be established; or when the relevant information is absent.Do not turn a claim into entailment simply because it sounds plausible or discusses the same topic. Do not turn it into contradiction merely because the source does not mention it.
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
You receive a complete booklet in German, French or Italian, with pages marked [[PAGE n]], the name of ONE vote, and a claim that may be in another language. The booklet may cover several proposals. Use only information relevant to the named vote.
{RULES}
Evidence requirements:
- First decide the correct label using the claim and the supplied booklet. Do not change the label merely to make it easier to provide evidence.
- If the label is "neutral", return exactly `"evidence": []`. Do not include any evidence items.
- If the label is "entailment", return 1 to 3 evidence items. Use **1 item** when a single passage clearly supports the entire claim. Use **2 items** when separate passages establish different essential parts of the claim. Use **3 items** only when three distinct passages are needed to establish multiple essential details or clarify the meaning together. Every item must directly support the claim; do not add items merely to reach a target.
- If the label is "contradiction", return 1 to 3 evidence items. Use **1 item** when a single passage clearly establishes the direct conflict. Use **2 items** when one passage establishes part of the conflict and another establishes a necessary detail, such as the correct actor, vote, or proposal. Use **3 items** only when multiple distinct passages are necessary to establish the conflict fully. Every item must establish or clarify an actual contradiction; passages about the same topic are not sufficient.
- Select evidence only after deciding the label. Evidence should demonstrate why the decision is correct, not determine the decision by itself.
- A passage can support a claim through equivalent meaning, paraphrase or translation. Exact wording is not required for entailment, but the evidence itself must be copied verbatim from the booklet.
- When the source neither supports nor directly conflicts with the claim, choose neutral even if related passages exist. When the source clearly supports or contradicts the claim, do not choose neutral simply because the wording differs.
- Use the correct 1-based PDF page number shown in the `[[PAGE n]]` marker. Include only the shortest passage that preserves the relevant meaning, qualifications, conditions, negation and attribution.
- Each evidence item must contain the relevant text and be no longer than 4,000 characters. Do not include unrelated passages, duplicate quotes, headings alone, URLs or filler.
- Return valid JSON only, with no explanation outside the JSON.
Required format:
{{"label": "entailment|neutral|contradiction", "evidence": [{{"page": 1, "text": "verbatim passage"}}]}}"""

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
