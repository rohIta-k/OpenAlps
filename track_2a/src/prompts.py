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
- For entailment, quote passage(s) that support the claim's meaning.
- For contradiction, quote passage(s) that establish the actual conflict with the claim. Do not quote only a passage about the same topic.
- For neutral, must return an empty evidence list: [].
- Return 1 to 3 evidence items for entailment or contradiction, depending on what is needed to establish the label. One precise passage is sufficient when it clearly establishes the decision. Use 2 or 3 when additional passages provide complementary support, establish different essential details, or clarify an otherwise ambiguous passage. Do not add items just to reach a target.
- Evidence may be semantically relevant even when its wording differs from the claim, but it must genuinely support the classification. Topic similarity alone is not sufficient.
- Prefer the detailed section about the named vote over a short front-page summary when it provides stronger evidence.
- Copy evidence verbatim in the booklet's original language. Never translate or paraphrase the evidence.
- Each item must contain the correct 1-based PDF page number and the relevant text.
- Prefer the shortest passage that fully preserves the relevant meaning, including necessary qualifications, conditions, negation and attribution. Include surrounding sentences when needed to avoid changing the meaning.
- Each evidence item must be no longer than 4,000 characters. Never return an entire page unless the relevant evidence genuinely requires that much context.
- Do not include unrelated passages, duplicate quotes, page headings alone, URLs or filler.
- Use the page number shown in the [[PAGE n]] marker.
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
