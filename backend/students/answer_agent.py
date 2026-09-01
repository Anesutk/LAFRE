"""
Agentic answer-writing pipeline (v2 - composable primitives).

Earlier versions of this file gave the model ~24 large, overlapping "response type" tools
(write_case_summary, write_legal_risk, write_contract_review, etc). That was replaced on
purpose: too many similar-shaped tools makes tool SELECTION less reliable for a small/cheap
model, which is exactly backwards for an app that wants consistently good answers. This version
gives the model a small set of low-level formatting primitives instead - the same building
blocks any well-formatted legal explainer is actually made of - and lets it compose them
freely into a case summary, an IRAC analysis, a rights explainer, or anything else, rather than
picking one pre-baked macro template.

There is no legacy/keyword-routed fallback pipeline anymore (removed on purpose, at the
project owner's request). If the agent fails, generate_agentic_answer returns None and the
caller in views.py raises a clean, honest error to the student - it does not silently degrade
to older, worse-quality output.

Two things are still handled in Python, not by the model:
- Numbered/bulleted lists are always rendered from a real Python list, never typed by the model
  as raw markdown text - this is what makes the "1. 1. 1." bug structurally impossible.
- Page citations can only reference a page that was actually returned by search_sources for
  THIS answer - the model cannot invent one.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from . import generation as legacy

try:
    from strands import Agent, tool
    from strands.models import BedrockModel
    STRANDS_AVAILABLE = True
except Exception:  # pragma: no cover
    STRANDS_AVAILABLE = False
    Agent = None  # type: ignore
    BedrockModel = None  # type: ignore

    def tool(fn):  # type: ignore
        return fn


ANSWER_SYSTEM_PROMPT = """
You are the answer-writing agent for LAFRE, a Zimbabwe law-study app. You are a small, fast
model, so follow these rules literally rather than improvising around them.

HOW YOU WORK: you do not write markdown directly. You build the answer by calling tools, in
whatever order and combination the question actually needs, then you are done - you never
output a final text message yourself, only tool calls.

STEP 0 - READ THE CHAT CONTEXT FIRST, BEFORE DECIDING ANYTHING ELSE. This is the step most
likely to be gotten wrong, so read it twice:
- If the student's message is short and clearly refers back to what you were just discussing
  ("what is it", "explain", "why", "go on", "and if not", "what about X" where X was already
  the subject) - resolve it against the ACTUAL topic in the chat context, do not treat it as a
  standalone question and do not ask what they mean.
- If your OWN immediately preceding message asked a clarifying question, and the student's new
  message is a short confirmation, correction, or answer to it ("yes", "no", "the second one",
  or simply naming the thing you asked about) - that confirms/resolves your question. Proceed
  straight to answering using the resolved topic. Do NOT call ask_clarifying_question again for
  the same thing you already asked - re-asking after the student already answered is a bug.
  Example: you asked "Did you mean the Control of Goods Act instead of the Sales of Goods Act?"
  and the student replies "yes" -> you now explain the Control of Goods Act. You do not ask
  again "did you mean the Control of Goods Act or...".
- If a topic name you were given doesn't exactly match anything in search_sources, DON'T just
  ask a clarifying question and stop - search for the closest plausible match instead (e.g.
  "Sale of Goods Act" not existing in Zimbabwe -> search "Control of Goods Act", the real
  equivalent), answer using that best guess, then call note_assumption to flag what you
  assumed. Only fall back to ask_clarifying_question (see Step 4) when you genuinely cannot
  make any reasonable guess at all - e.g. "explain that" with truly nothing in the chat to
  resolve it against. See the note_assumption and ask_clarifying_question tool descriptions
  below for exactly when to use each.
- If this question has its own clear new topic, unrelated to recent chat, answer the new topic
  - do not drag the old topic in just because the chat has history.
- CRITICAL: when a message is vague and refers back to something ("give me things worth 20
  marks", "do the first one", "what about that") - the resolved topic MUST be something that
  was ACTUALLY discussed earlier in this exact chat. Never substitute a different, unrelated
  legal topic that was never mentioned, even if it is superficially similar (e.g. the chat
  discussed "offer vs invitation to treat" and "civil vs criminal law" - a vague follow-up
  must resolve to one of THOSE, never to an unrelated topic like "bail vs bond" that nobody
  asked about). If you are not sure which earlier topic a vague message refers to, ask via
  ask_clarifying_question rather than guessing a new one.
- If the student indicates your previous answer was wrong, off-topic, or not what they asked
  for, do not repeat that same answer again - actually re-read their correction and the chat
  history and produce a different, correctly-resolved answer.

STEP 0B - SCOPE. This app is for legal-study questions: law concepts, cases, statutes, legal
writing, exam-style answers, and the student's own uploaded law notes. If a message is clearly
unrelated to any of that (e.g. general chit-chat, coding help, unrelated homework), do not call
search_sources - just call write_paragraph with a brief, friendly note that you're built for
legal-study questions, then suggest_next with a couple of example legal-study prompts. Do not
apply this narrowly - legal questions can be phrased informally and still count.

STEP 1 - ALWAYS retrieve first. Call search_sources with the clean, resolved topic before
writing anything, even if you are confident you already know the answer. If it returns nothing
relevant, say so honestly (via write_paragraph) instead of answering from memory as if you had
a source - study answers must be grounded, and must never contradict what search_sources
actually returned. Never write about a topic that is neither the resolved topic from Step 0
nor something search_sources actually returned - if you notice yourself about to introduce a
topic nobody asked about, stop and re-resolve instead.

STEP 1A - BREAK THE QUESTION INTO ITS REAL SUB-PARTS BEFORE WRITING ANYTHING. A short question
is still made of several things a complete answer needs to cover - decide what those are before
you start calling content tools, the same way a good teacher plans an answer before speaking.
For example: "what is milk" is really asking (1) what milk is, (2) where it comes from, (3)
what it's made of / its composition, (4) why it matters / its benefit. "Summarise the Sales
Act" is really asking (1) what the Act actually says/covers, (2) when and why it was made,
(3) its key provisions or effect, (4) its practical benefit/significance. Search for and
address each real sub-part your specific question implies - do not guess at a fixed universal
list, work out the sub-parts THIS question actually has. This is what makes an answer feel
complete instead of narrow, and it is what mark-based depth (Step 1B) is calibrated against -
skipping this step is the most common way an answer ends up too thin. A part of this is
choosing which of the block tools (Step 2) best presents each sub-part - a definition sub-part
usually wants write_label, a "why it matters" sub-part usually wants a short write_paragraph,
several distinct points usually want write_bullets, etc.

STEP 1B - MARK ALLOCATION. If the student states or implies a mark value ("(20 marks)",
"worth 20 marks", "give me a 10 mark answer"), that number sets how much substance the answer
needs, not just its length:
- Roughly 1-5 marks: a direct, focused answer - one clear point, well explained. Usually
  write_label or a short write_paragraph is enough.
- Roughly 6-15 marks: several distinct points genuinely developed, not just listed - each
  point needs its own explanation, not a one-line mention. Use write_heading to separate
  distinct parts, write_bullets or write_numbered for the points themselves, each with real
  substance, not a bare phrase.
- Roughly 16-25+ marks: exam-level depth - use write_legal_analysis-style structure via
  write_heading (Issue/Rule/Application/Conclusion or a comparable structure fitting the
  question), and make sure EVERY distinct issue, element, or side of a comparison the question
  raises is actually covered with its own developed explanation, not summarised in one
  sentence. A 20-mark comparison question needs both concepts' full definitions, several
  points of distinction each properly explained, and a real conclusion - not the same content
  you'd give for a plain unmarked question.
The number of marks is a proxy for how many distinct, well-developed points a marker would
expect - use it to judge whether you have covered the topic thoroughly enough, not as a
target word count to pad toward.

STEP 2 - BUILD THE ANSWER FROM THESE PRIMITIVES. Combine whichever of these best represent
THIS specific answer - they are building blocks, not fixed modes, and most real answers use
several together:
- write_heading - section titles, when the answer has more than one distinct part.
- write_paragraph - explanatory prose. Use **bold** inline for key terms.
- write_label - "**Label:** explanation" shape. This is your most versatile tool - use it for
  a term-then-definition ("**Consideration:** ..."), a question-then-answer ("**What is a
  valid contract?** ..."), a short example ("**Example:** ..."), or a short conclusion
  ("**In summary:** ...").
- write_bullets - unordered points; pass nested sub-points via each item's "children" list when
  a point has supporting detail under it.
- write_numbered - ordered steps, elements, requirements, or a legal test's stages. Never type
  numbers as plain text inside write_paragraph - that is exactly the bug write_numbered exists
  to prevent.
- write_note - a short highlighted note, warning, or caveat that should stand out (e.g.
  jurisdiction caveats, "this depends on the facts", high-stakes warnings).
- write_quote_block - exact wording the student needs to inspect precisely (a clause, a
  statute's actual text) - only quote text that genuinely came from search_sources.
- write_table - any structured/tabular comparison (including "X vs Y" questions - use headers
  like ["Aspect", "X", "Y"]).
Match structure to the question, using the sub-parts you identified in Step 1A: most real
questions genuinely have 2-4 sub-parts (definition, source/origin, key features, significance,
etc) and deserve one block per sub-part - a single write_paragraph is usually too thin unless
the question is truly a one-fact lookup ("what year was X decided"). A genuinely complex
question (case analysis, contract review, multi-part rights question) needs more blocks still,
with headings separating the parts. Depth should come from the question's real sub-parts, not
from a rigid template, and not from padding a single fact with filler.

CRITICAL FORMATTING RULE: never type a bullet character ("*", "-", "•") or a number ("1.")
inside write_paragraph or write_label text - if you have more than one point to make, call
write_bullets or write_numbered instead. Mixing manually-typed list markers into prose text is
exactly the poorly-formatted, run-together output this system exists to prevent.

CRITICAL TOOL-USE RULE: you write blocks ONLY by actually calling the tools below through
function-calling. NEVER write the text/syntax of a tool call as part of an answer (e.g. never
output something like "[cite_page(source_id='K1', page='')]" as visible content) - if you
intend to cite a page, actually call cite_page as a real tool call, don't narrate it.

STEP 3 - FLASHCARDS. If asked for flashcards, and the topic is at all complex, call
write_heading/write_paragraph or write_label FIRST to establish the concept, THEN
write_flashcards - flashcards work best as a check on understanding after a short explanation,
not as the entire answer with nothing around them. For a narrow/simple topic a one-line
write_paragraph intro is enough before the cards.

STEP 4 - CITATIONS. If a specific page/section was returned by search_sources for a source you
are using, call cite_page with that exact source_id and page. Never invent a page number that
was not actually in the search_sources result for that source. Never invent a case name, a
related case, a book, an article, or a "further reading" suggestion that did not come from
search_sources - if you want to mention a related authority, only do so if search_sources
actually returned it; otherwise leave it out entirely rather than naming something you are not
sure is real.
If the student is asking you to REFERENCE or CITE something - phrases like "reference this",
"cite this", "give me a citation", "how do I reference X", "can you reference this act/case for
me" - this is a request for write_citation_cards, not a normal explanation and not a "legal
research summary" describing the source. Make sure you know exactly which phrase/claim needs citing
and which source it should come from (ask via ask_clarifying_question if that is not already
obvious from the conversation), then call write_citation_cards using the real source_id(s) from
search_sources - the tool rejects any source_id that wasn't actually returned by
search_sources, so you cannot cite something you didn't retrieve. Do not answer a referencing
request with write_paragraph/write_heading prose describing the source - that is not what
"reference this" means.

CASE NAMES ARE NOT OPTIONAL TO GET RIGHT: a fabricated case name, quote, or paragraph
reference is worse than saying nothing, because it is presented to a student as real legal
authority. Only mention a case by name, quote it, or give it a pinpoint reference (para/page
number) if that exact case name appears in a search_sources result for this turn. If you want
to illustrate a point with a case example and nothing specific came back from search_sources,
say so plainly ("a case example was not found for this in the available sources") instead of
inventing a plausible-sounding case name - this applies in plain prose, not only in citation
cards or cite_page.

STEP 4B - NEVER REPEAT YOURSELF. Each block you add must contain information the student
hasn't already been given in an earlier block of THIS SAME answer. A very common mistake is
covering the same list of points three times in one answer - once as prose, again as bullet
points, again as flashcards or a "key takeaways" recap. Say each thing ONCE, in whichever
single block suits it best, then move on. If you are about to write something that restates an
earlier block in slightly different words, stop and either add genuinely new information or
omit that block.

STEP 4C - after search_sources, call mark_source_relevant once for each source you actually
used in the answer (whether or not you also called cite_page on it), so the student can see
why each source appears in the Sources panel. Skip sources you looked at but didn't end up
using.

STEP 5 - never name a source/document by its literal title in your prose (e.g. never write
"according to Prof Docs"). Sources are already shown to the student separately as cards -
referring to legal authorities like "the Constitution" or "the Sale of Goods Act" by their real
legal name is fine and expected; naming an uploaded file's internal title is not.

STEP 6 - always finish by calling suggest_next with 2-3 short follow-up prompts a good tutor
would offer next, based on what THIS answer just covered - a related concept, a deeper
question, or a practical application. Never generic ("ask a question") - tie them to the
actual topic just discussed.

Write for a law student who wants to understand the material, not to sound impressive. Use
plain, clear, confident language - do not hedge every sentence, but do not state something as
certain when search_sources did not actually support it either.
""".strip()


def _answer_model():
    model_id = (
        os.environ.get("BEDROCK_AGENT_MODEL_ID")
        or legacy.bedrock_model_id("thinking")
    )
    return BedrockModel(model_id=model_id, max_tokens=3000, temperature=0.3)


TOOL_STATUS_LABELS = {
    "search_sources": "Searching legal sources…",
    "write_heading": "Structuring the answer…",
    "write_paragraph": "Writing the explanation…",
    "write_label": "Writing the explanation…",
    "write_bullets": "Listing key points…",
    "write_numbered": "Listing the steps…",
    "write_note": "Adding a note…",
    "write_quote_block": "Quoting the source…",
    "write_table": "Building a table…",
    "write_flashcards": "Creating flashcards…",
    "write_citation_cards": "Preparing citation cards…",
    "mark_source_relevant": "Checking source relevance…",
    "cite_page": "Adding a page citation…",
    "ask_clarifying_question": "Thinking of a clarifying question…",
    "suggest_next": "Wrapping up…",
}


def generate_agentic_answer(
    *,
    user,
    question: str,
    depth: str = "normal",
    history_summary: str = "",
    prior_sources: Optional[List[Dict[str, Any]]] = None,
    progress_callback=None,
) -> Optional[Dict[str, Any]]:
    if not STRANDS_AVAILABLE:
        return None
    try:
        model = _answer_model()
    except Exception:
        return None

    state: Dict[str, Any] = {
        "sources": {},          # id -> SourceItem
        "blocks": [],           # ordered list of rendered markdown fragments
        "flashcards": [],
        "citation_cards": [],
        "clarify": None,
        "next_steps": [],
        "used_source_ids": [],
    }

    @tool
    def search_sources(topic: str, source_type: str = "all") -> str:
        """Search the knowledge base and the student's uploaded documents for a topic. ALWAYS
        call this before writing anything, using the RESOLVED topic (after applying Step 0).
        Returns each result's id, title, an excerpt, and a page/section number if available -
        use the id later with cite_page or write_citation_cards, and only cite a page number
        that actually appears in this result.
        Args:
            topic: the clean, resolved topic/question to search for.
            source_type: "all", "constitution", "statute", "case_law", or "study_note".
        """
        results = legacy._search_knowledge_base(topic, source_type=source_type, limit=6)
        if user and getattr(user, "id", None):
            results += legacy._search_uploaded_documents(user_id=user.id, query=topic, limit=6)
        summary = []
        for item in results:
            state["sources"][item.id] = item
            summary.append({
                "id": item.id, "title": item.title, "pages": item.pages,
                "excerpt": item.excerpt[:500], "kind": item.kind,
            })
        return json.dumps(summary, ensure_ascii=False) if summary else "No relevant sources found."

    @tool
    def write_heading(text: str, level: int = 2) -> str:
        """Add a section heading. Use level 2 for a main section, 3 for a subsection.
        Args:
            text: the heading text (no markdown hashes, just the words).
            level: 2 or 3.
        """
        hashes = "##" if level <= 2 else "###"
        state["blocks"].append({"type": "text", "content": f"{hashes} {text.strip()}"})
        return "added"

    @tool
    def write_paragraph(markdown: str) -> str:
        """Add explanatory prose. Plain markdown paragraph(s) - use **bold** for key terms
        inline. No manually typed numbered/bulleted lists (use write_numbered/write_bullets).
        Args:
            markdown: the prose to add.
        """
        if markdown and markdown.strip():
            state["blocks"].append({"type": "text", "content": markdown.strip()})
        return "added"

    @tool
    def write_label(label: str, text: str) -> str:
        """The single most versatile block: "**Label:** explanation". Use it for a term then
        its definition, a question then its answer, a short example, or a short conclusion -
        whatever fits, by choosing what you pass as `label`.
        Args:
            label: the bold lead-in, e.g. "Consideration", "What is a valid contract?",
                "Example", "In summary".
            text: the explanation/answer/example/conclusion that follows.
        """
        state["blocks"].append({"type": "text", "content": f"**{label.strip()}**  \n{text.strip()}"})
        return "added"

    @tool
    def write_bullets(items: List[Dict[str, Any]]) -> str:
        """Add an unordered list. Supports nesting.
        Args:
            items: list of {"text": "point"} or {"text": "point", "children": ["sub-point",
                "sub-point"]} for nested detail under a point.
        """
        lines = []
        for it in items or []:
            text = str(it.get("text", "")).strip() if isinstance(it, dict) else str(it).strip()
            if not text:
                continue
            lines.append(f"- {text}")
            for child in (it.get("children") if isinstance(it, dict) else None) or []:
                child = str(child).strip()
                if child:
                    lines.append(f"  - {child}")
        if lines:
            state["blocks"].append({"type": "text", "content": "\n".join(lines)})
        return "added"

    @tool
    def write_numbered(items: List[str], intro: str = "") -> str:
        """Add a numbered list. Numbers are generated automatically - never include numbers
        yourself inside item text.
        Args:
            items: the list items, each WITHOUT a leading number.
            intro: optional one short line introducing the list.
        """
        cleaned = [str(i).strip().lstrip("0123456789.) ") for i in items or [] if str(i).strip()]
        if cleaned:
            lines = [f"{idx}. {t}" for idx, t in enumerate(cleaned, start=1)]
            content = (f"{intro.strip()}\n\n" if intro and intro.strip() else "") + "\n".join(lines)
            state["blocks"].append({"type": "text", "content": content})
        return "added"

    @tool
    def write_note(text: str) -> str:
        """Add a short highlighted note/warning/caveat that should visually stand out from
        normal prose (e.g. a jurisdiction caveat, a high-stakes warning).
        Args:
            text: the note content, one or two sentences.
        """
        state["blocks"].append({"type": "text", "content": f"> **Note:** {text.strip()}"})
        return "added"

    @tool
    def write_quote_block(text: str, source_id: str = "", label: str = "") -> str:
        """Quote exact wording the student needs to inspect precisely - a clause, a statute's
        actual text. Only use text that genuinely came from search_sources; never fabricate
        wording and present it as a quote. Always pass source_id when quoting something
        specific - the quote is checked against that source's actual retrieved text, and
        rejected if it doesn't appear there.
        Args:
            text: the exact wording being quoted.
            source_id: the id from a prior search_sources result this quote comes from.
            label: optional short label, e.g. "Section 5(2)".
        """
        if source_id:
            src = state["sources"].get(source_id)
            if not src:
                return "rejected: that source_id was not in the search_sources results"
            normalise = lambda s: re.sub(r"\s+", " ", s or "").strip().lower()
            if normalise(text)[:60] not in normalise(getattr(src, "excerpt", "")):
                return "rejected: this text does not appear in that source's retrieved excerpt - do not fabricate quotes"
        prefix = f"**{label.strip()}**  \n" if label and label.strip() else ""
        state["blocks"].append({"type": "text", "content": f"{prefix}> {text.strip()}"})
        return "added"

    @tool
    def write_table(caption: str, headers: List[str], rows: List[List[str]]) -> str:
        """Add a markdown table - for any tabular/structured comparison, including "X vs Y"
        questions (use headers like ["Aspect", "X", "Y"]).
        Args:
            caption: a one-line caption shown above the table (can be empty).
            headers: column headers.
            rows: each row's cells, same length as headers.
        """
        if headers and rows:
            head = "| " + " | ".join(str(h) for h in headers) + " |"
            sep = "| " + " | ".join("---" for _ in headers) + " |"
            body = "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows if row)
            content = (f"{caption.strip()}\n\n" if caption and caption.strip() else "") + f"{head}\n{sep}\n{body}"
            state["blocks"].append({"type": "text", "content": content})
        return "added"

    @tool
    def write_flashcards(cards: List[Dict[str, str]]) -> str:
        """Add flashcards. Each front MUST be a real question ending in "?" of at least 5
        words (not a one-word prompt) - phrase a definition card as "What is X?" rather than
        just "X". Cards that don't meet this are dropped silently, so write them properly the
        first time.
        Args:
            cards: list of {"front": "...?", "back": "..."} objects.
        """
        kept = []
        for c in cards or []:
            front = str(c.get("front", "")).strip()
            back = str(c.get("back", "")).strip()
            if front.endswith("?") and len(front.split()) >= 5 and back:
                kept.append({"front": front[:300], "back": back[:1500]})
        state["flashcards"].extend(kept)
        return f"added {len(kept)} valid card(s)" if kept else "no valid cards (need a real question, 5+ words, ending in '?')"

    @tool
    def write_citation_cards(items: List[Dict[str, str]]) -> str:
        """Add copiable citation cards for referencing a source. Each item MUST reference a
        real source_id from a prior search_sources call - items without a matching source_id
        are rejected automatically, so you cannot fabricate a citation even by mistake. Never
        invent a case name, quote, or pinpoint reference that isn't backed by an actual
        search_sources result.
        Args:
            items: list of {"source_id": "id from search_sources", "phrase": "the claim/quote
                being cited", "in_text": "the in-text citation, e.g. (Author, Year)",
                "full_reference": "the full end-text/bibliography entry"}.
        """
        kept = []
        for it in items or []:
            source_id = str(it.get("source_id", "")).strip()
            phrase = str(it.get("phrase", "")).strip()
            in_text = str(it.get("in_text", "")).strip()
            full_ref = str(it.get("full_reference", "")).strip()
            if source_id not in state["sources"]:
                continue  # silently reject - not backed by a real retrieved source
            if in_text and full_ref:
                kept.append({"phrase": phrase[:300], "in_text": in_text[:200], "full_reference": full_ref[:400]})
                if source_id not in state["used_source_ids"]:
                    state["used_source_ids"].append(source_id)
        state["citation_cards"].extend(kept)
        if not kept and items:
            return "rejected: none of these source_id values matched an actual search_sources result"
        return f"added {len(kept)} citation card(s)" if kept else "no valid citations (need source_id, in_text and full_reference)"

    @tool
    def mark_source_relevant(source_id: str, why_relevant: str) -> str:
        """Explain why a specific retrieved source was actually used in this answer - shown to
        the student in the Sources panel next to that source. Call this for every source from
        search_sources that meaningfully informed your answer (not ones you looked at and
        didn't use).
        Args:
            source_id: the id from a prior search_sources result.
            why_relevant: one short sentence, e.g. "Defines the elements this answer explains."
        """
        src = state["sources"].get(source_id)
        if not src:
            return "rejected: unknown source_id"
        try:
            src.relevance = why_relevant.strip()[:200]  # type: ignore[attr-defined]
        except Exception:
            pass
        if source_id not in state["used_source_ids"]:
            state["used_source_ids"].append(source_id)
        return "added"

    @tool
    def cite_page(source_id: str, page: str, excerpt: str) -> str:
        """Attach a specific page/section citation to the answer. Only works for a
        source_id/page that search_sources actually returned - fabricated ones are rejected.
        Args:
            source_id: the id from a prior search_sources result.
            page: the page/section number from that same result.
            excerpt: a short (<40 word) quote or paraphrase of what that page says.
        """
        src = state["sources"].get(source_id)
        if not src or not src.pages or str(page).strip() not in str(src.pages):
            return "rejected: that source_id/page was not in the search_sources results"
        state["blocks"].append({"type": "text", "content": f"> On {src.title}, page {page}: {excerpt.strip()}"})
        try:
            src.summary = excerpt.strip()  # type: ignore[attr-defined]
        except Exception:
            pass
        if source_id not in state["used_source_ids"]:
            state["used_source_ids"].append(source_id)
        return "added"

    @tool
    def note_assumption(assumption: str) -> str:
        """Use this INSTEAD of ask_clarifying_question whenever you can make a reasonable guess
        at what the student meant and something relevant was found for it - answer using that
        best guess (call the normal content tools as usual), then call this to flag the
        assumption at the end, so the student can correct you in one reply instead of getting
        blocked with no content. This should be your DEFAULT for ambiguity - only use
        ask_clarifying_question when you genuinely cannot make any reasonable guess at all.
        Args:
            assumption: one short sentence, e.g. "I've assumed you meant the Control of Goods
                Act, since Zimbabwe does not have a separate Sale of Goods Act - let me know if
                you meant something else."
        """
        state["blocks"].append({"type": "text", "content": f"> {assumption.strip()}"})
        return "added"

    @tool
    def ask_clarifying_question(question: str, reason: str) -> str:
        """Call this INSTEAD of answering ONLY when the question is so ambiguous or so far off
        from anything in search_sources that no reasonable best-guess answer is possible at
        all. This should be rare - if you can make ANY reasonable guess with something relevant
        found, answer using that guess and call note_assumption instead, don't block the
        student with no content. Do not combine with other tools in the same turn. Do not call
        this twice in a row for the same topic - if you already asked once and the student
        replied, resolve it (see Step 0) rather than asking again.
        Args:
            question: the clarifying question to show the student.
            reason: one short internal note on why (not shown verbatim, for logging).
        """
        state["clarify"] = question.strip()
        return "clarification requested"

    @tool
    def suggest_next(prompts: List[str]) -> str:
        """Always call this last (skip only if you called ask_clarifying_question instead):
        2-3 short follow-up prompts a good tutor would suggest next, specific to what this
        answer just covered.
        Args:
            prompts: 2-3 short prompt strings.
        """
        state["next_steps"] = [str(p).strip() for p in (prompts or []) if str(p).strip()][:3]
        return "added"

    def _on_agent_event(**kwargs):
        # Real progress events from Strands, fired as each tool is actually invoked - not a
        # simulated/fake progress bar. See strandsagents.com callback-handlers docs.
        if not progress_callback:
            return
        try:
            tool_use = kwargs.get("current_tool_use")
            if tool_use and tool_use.get("name"):
                label = TOOL_STATUS_LABELS.get(tool_use["name"], "Working on your answer…")
                progress_callback(label)
        except Exception:
            pass

    try:
        agent = Agent(
            name="LAFREAnswerAgent",
            model=model,
            system_prompt=ANSWER_SYSTEM_PROMPT,
            tools=[
                search_sources, write_heading, write_paragraph, write_label, write_bullets,
                write_numbered, write_note, write_quote_block, write_table, write_flashcards,
                write_citation_cards, mark_source_relevant, cite_page, note_assumption,
                ask_clarifying_question, suggest_next,
            ],
            callback_handler=_on_agent_event if progress_callback else None,
        )
        envelope = (
            f"Student's latest message: {question}\n\n"
            f"Recent chat history, most recent last (apply Step 0 to this - resolve short "
            f"follow-ups and confirmations against it; ignore it if this message has its own "
            f"clear new topic): {history_summary or 'None - this is a new chat.'}\n\n"
            f"Answer depth requested: {depth}."
        )
        agent(envelope)
    except Exception:
        return None

    if state["clarify"]:
        return {
            "mode": "clarify",
            "answer_style": depth,
            "title": "Quick check",
            "markdown": legacy.strip_leaked_tool_calls(state["clarify"]),
            "source_badges": [],
            "documents": [],
            "flashcards": [],
            "citation_cards": [],
            "next_steps": [],
        }

    if not state["blocks"] and not state["flashcards"] and not state["citation_cards"]:
        return None  # model produced nothing usable

    # Drop any heading block with nothing actually under it - a heading followed immediately
    # by another heading of the SAME level (or sitting last with nothing after it) means the
    # model called write_heading without following through, which reads as a missing/broken
    # section. A heading followed by a deeper subheading is legitimate nesting and is kept.
    def _heading_level(block):
        content = block["content"]
        if content.startswith("### "):
            return 3
        if content.startswith("## "):
            return 2
        return None

    cleaned_blocks = []
    for i, block in enumerate(state["blocks"]):
        level = _heading_level(block)
        if level is not None:
            next_block = state["blocks"][i + 1] if i + 1 < len(state["blocks"]) else None
            next_level = _heading_level(next_block) if next_block else None
            is_empty = next_block is None or (next_level is not None and next_level <= level)
            if is_empty:
                continue  # empty heading - skip it
        cleaned_blocks.append(block)

    markdown = "\n\n".join(b["content"] for b in cleaned_blocks).strip()
    all_sources = list(state["sources"].values())
    markdown = legacy.clean_model_text(markdown) if markdown else markdown
    markdown = legacy.strip_leaked_tool_calls(markdown) if markdown else markdown
    markdown = legacy.normalise_numbered_lists(markdown) if markdown else markdown
    markdown = legacy.scrub_document_names(markdown, all_sources) if markdown else markdown

    used_sources = [s for s in all_sources if s.score is None or s.score >= legacy.KB_MIN_SCORE] or all_sources

    def _badge(s):
        d = s.as_dict()
        summary = getattr(s, "summary", None)
        if summary:
            d["excerpt"] = summary
        elif d.get("excerpt"):
            text = d["excerpt"]
            if len(text) > 300:
                cut = text[:300]
                boundary = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
                d["excerpt"] = (cut[: boundary + 1] if boundary > 100 else cut) + "…"
        d["relevance"] = getattr(s, "relevance", None) or "Retrieved as a relevant source for this answer."
        return d

    fallback_markdown = "Here are the flashcards for this." if state["flashcards"] else "Here are the reference cards you asked for."

    return {
        "mode": "agentic",
        "answer_style": depth,
        "title": question[:60],
        "markdown": markdown or fallback_markdown,
        "source_badges": [_badge(s) for s in used_sources[:6]],
        "documents": [_badge(s) for s in used_sources[:6] if s.can_open],
        "flashcards": state["flashcards"],
        "flashcard_title": (question[:60] if state["flashcards"] else None),
        "citation_cards": state["citation_cards"],
        "next_steps": state["next_steps"],
    }
