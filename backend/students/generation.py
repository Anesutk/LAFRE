from __future__ import annotations

import json
import os
import re
from django.core import signing
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.conf import settings

try:
    from strands import Agent, tool  # type: ignore
    from strands.models import BedrockModel  # type: ignore
    STRANDS_AVAILABLE = True
except Exception:  # pragma: no cover
    STRANDS_AVAILABLE = False
    Agent = None  # type: ignore
    BedrockModel = None  # type: ignore

    def tool(fn):  # type: ignore
        fn.is_lafre_tool = True
        return fn


DEFAULT_KB_ID = ""
SOURCE_COLOURS = ["green", "blue", "amber", "purple", "rose", "slate"]

STOPWORDS = {
    "what", "this", "that", "with", "from", "about", "into", "give", "explain", "please", "could",
    "would", "does", "have", "where", "when", "which", "your", "they", "them", "then", "than",
    "make", "turn", "answer", "question", "student", "the", "and", "for", "are", "you", "can",
    "should", "need", "want", "document", "documents", "notes", "source", "sources", "law",
    "legal", "information", "show", "find", "read", "study", "material", "materials",
}

DISCLAIMER_STUDENT = "Legal information, not legal advice."




@dataclass


@dataclass
class SourceItem:
    id: str
    title: str
    excerpt: str = ""
    reason: str = ""
    kind: str = "source"
    open_url: str = ""
    download_url: str = ""
    pages: str = ""
    colour: str = "green"
    score: Optional[float] = None
    can_open: bool = False
    download_name: str = ""
    source_uri_token: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "excerpt": self.excerpt,
            "reason": self.reason,
            "kind": self.kind,
            "open_url": self.open_url,
            "download_url": self.download_url,
            "pages": self.pages,
            "colour": self.colour,
            "score": self.score,
            "can_open": self.can_open,
            "download_name": self.download_name or self.title,
            "source_uri_token": self.source_uri_token,
        }


@dataclass


def safe_title(name: str) -> str:
    title = Path(str(name or "Source")).name
    redactions = [
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "aws_access_key_id", "aws_secret_access_key",
        "s3://", "arn:aws", "X-Amz-Credential", "X-Amz-Signature", "AWS_SESSION_TOKEN",
    ]
    for item in redactions:
        title = title.replace(item, "[redacted]")
    title = re.sub(r"(?i)access[_-]?key[_-]?id\s*[=:]\s*\S+", "[redacted]", title)
    title = re.sub(r"(?i)secret[_-]?access[_-]?key\s*[=:]\s*\S+", "[redacted]", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title or "Source"


def clean_display_title(name: str) -> str:
    """Return a user-facing source title without file extensions or technical paths."""
    title = safe_title(name)
    title = re.sub(r"(?i)\.(pdf|docx?|txt|md|csv|rtf)$", "", title).strip()
    title = title.replace("_", " ").replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title or "Source"


def sign_kb_s3_source(s3_uri: str, title: str = "") -> str:
    if not s3_uri or not str(s3_uri).startswith("s3://"):
        return ""
    try:
        return quote(signing.dumps({"s3_uri": s3_uri, "title": safe_title(title)}, compress=True), safe="")
    except Exception:
        return ""


def clean_model_text(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"```(?:markdown|md|json)?\s*", "", text, flags=re.I)
    text = text.replace("```", "")
    text = text.replace("\r\n", "\n")
    # Remove accidental visible prompt/tool labels.
    text = re.sub(
        r"(?im)^\s*(system prompt|planner|orchestrator|formatter|tool used|document_search_agent|flashcard_agent)\s*:.*$",
        "",
        text,
    )
    # Avoid excessive heading hashes; renderer will clean too, but keep the model output neat.
    text = re.sub(r"(?m)^#{4,}\s*", "### ", text)
    # Sources are rendered as badges below the answer, so remove visible source-id citations from prose.
    text = re.sub(r"\s*\[(?:K|D|S)\d+\]", "", text)
    text = re.sub(r"(?im)^\s*(sources?|citations?|references?)\s*:\s*.*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = normalise_numbered_lists(text)
    return text.strip()


def scrub_document_names(text: str, sources: "List[SourceItem]") -> str:
    """The system prompt already tells the model never to name an UPLOADED document by its
    internal filename/title (sources are shown as separate badges/cards), but low-tier models
    don't always obey that reliably. This is a deterministic safety net.

    IMPORTANT: this only scrubs sources that are actually the user's own uploaded material
    (kind == "uploaded document"). Statutes, cases, and the constitution have real legal names
    that SHOULD appear in the answer (e.g. "the Official Secrets Act") - scrubbing those
    replaced correct, meaningful legal references with the meaningless phrase "the source
    material", which is worse than doing nothing. Only a genuinely uploaded file's arbitrary
    filename gets this treatment.
    """
    if not text or not sources:
        return text
    uploaded_titles = sorted(
        {(s.title or "").strip() for s in sources if s.title and len(s.title.strip()) >= 4 and s.kind == "uploaded document"},
        key=len, reverse=True,
    )
    if not uploaded_titles:
        return text
    for title in uploaded_titles:
        esc = re.escape(title)
        # "according to/as per/based on <Title>" -> drop the lead-in phrase entirely,
        # keeping the rest of the sentence intact.
        text = re.sub(
            rf"(?i)\b(?:according to|as (?:stated|noted|mentioned) in|as per|per|based on) (?:the )?[\"'\u201c]?{esc}[\"'\u201d]?,?\s*",
            "",
            text,
        )
        # Any remaining bare mention of the exact title -> generic phrase. Swallow a preceding
        # "the"/"a"/"an" so we don't produce "the the source material".
        text = re.sub(rf"(?i)\b(?:the|an?)\s+[\"'\u201c]?{esc}[\"'\u201d]?", "the source material", text)
        text = re.sub(rf"(?i)[\"'\u201c]?{esc}[\"'\u201d]?", "the source material", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^\s*,\s*", "", text)
    # A sentence that started with the stripped lead-in may now start lowercase; fix capitalisation.
    text = re.sub(r"(?m)^([a-z])", lambda m: m.group(1).upper(), text)
    return text


TOOL_CALL_LEAK_PATTERN = re.compile(
    r"\[?\b(?:cite_page|search_sources|write_\w+|ask_clarifying_question|suggest_next|mark_source_relevant)\("
    r"[^)]*\)\]?",
    re.IGNORECASE,
)


def strip_leaked_tool_calls(text: str) -> str:
    """Safety net for a real failure mode: a small model sometimes writes the SYNTAX of a tool
    call as visible text (e.g. "[cite_page(source_id='K1', page='')]") instead of actually
    invoking it. That should never reach the student. Strip anything matching a tool-call
    shape from the rendered markdown.
    """
    if not text:
        return text
    cleaned = TOOL_CALL_LEAK_PATTERN.sub("", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalise_numbered_lists(text: str) -> str:
    """Repair low-tier model output that repeats `1.` for every ordered item."""
    lines = text.split("\n")
    number = 0
    in_list = False
    output = []
    for line in lines:
        match = re.match(r"^(\s*)1[.)]\s+(.*)$", line)
        if match:
            number += 1
            in_list = True
            output.append(f"{match.group(1)}{number}. {match.group(2)}")
            continue
        if in_list and re.match(r"^\s*\d+[.)]\s+", line):
            number += 1
            output.append(re.sub(r"^(\s*)\d+[.)]\s+", rf"\g<1>{number}. ", line))
            continue
        if line.strip() and not line.startswith(" "):
            in_list = False
            number = 0
        output.append(line)
    return "\n".join(output)


def kb_id() -> str:
    return (
        os.getenv("BEDROCK_KB_ID")
        or os.getenv("AWS_KB_ID")
        or getattr(settings, "AWS_KB_ID", "")
        or DEFAULT_KB_ID
    ).strip()


def aws_region() -> str:
    return (os.getenv("AWS_REGION") or getattr(settings, "AWS_REGION", "us-east-1") or "us-east-1").strip()


def bedrock_model_id(depth: str = "normal") -> str:
    if depth == "thinking":
        return (
            os.getenv("BEDROCK_THINKING_MODEL_ID")
            or os.getenv("BEDROCK_SMART_MODEL_ID")
            or os.getenv("AWS_BEDROCK_MODEL_ID")
            or getattr(settings, "AWS_BEDROCK_MODEL_ARN", "")
            or "us.amazon.nova-lite-v1:0"
        )
    return (
        os.getenv("BEDROCK_FAST_MODEL_ID")
        or os.getenv("AWS_BEDROCK_MODEL_ID")
        or getattr(settings, "AWS_BEDROCK_MODEL_ARN", "")
        or "us.amazon.nova-lite-v1:0"
    )


def keywords_for_query(query: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_'-]{2,}", (query or "").lower())
    terms: List[str] = []
    for word in words:
        if word not in STOPWORDS and word not in terms:
            terms.append(word)
    return terms[:18]


KB_MIN_SCORE = float(os.getenv("LAFRE_KB_MIN_SCORE", "0.45"))


def important_query_terms(query: str) -> List[str]:
    """Return the terms that must guide KB/document matching.

    This prevents a broad KB result such as an unrelated Geneva Conventions file
    from being accepted for a Zimbabwe Constitution query.
    """
    terms = keywords_for_query(query)
    important: List[str] = []
    for term in terms:
        if term not in important and len(term) >= 4:
            important.append(term)
    # Keep statute/section numbers useful.
    for number in re.findall(r"\b\d{1,4}\b", query or ""):
        if number not in important:
            important.append(number)
    return important[:12]


def source_matches_query(source: SourceItem, query: str) -> bool:
    """Reject weak or obviously unrelated search results."""
    if source.kind == "error":
        return False
    terms = important_query_terms(query)
    if not terms:
        return True
    haystack = f"{source.title}\n{source.excerpt}\n{source.pages}\n{source.kind}".lower()
    hits = sum(1 for term in terms if term.lower() in haystack)
    # Section questions need at least the section number or an important topic term.
    if re.search(r"\bsection\s+\d+\b", (query or "").lower()):
        section_number = re.search(r"\bsection\s+(\d+)\b", (query or "").lower())
        if section_number and section_number.group(1) in haystack:
            return True
    if any(term in haystack for term in ["constitution", "constitutional"]) and any(term in (query or "").lower() for term in ["constitution", "constitutional"]):
        return True
    return hits >= 1


def filter_reliable_sources(sources: List[SourceItem], query: str, *, is_kb: bool = False) -> List[SourceItem]:
    reliable: List[SourceItem] = []
    for source in sources:
        if source.kind == "error":
            continue
        if is_kb and source.score is not None:
            try:
                if float(source.score) < KB_MIN_SCORE and not source_matches_query(source, query):
                    continue
            except Exception:
                pass
        if not source_matches_query(source, query):
            continue
        reliable.append(source)
    return reliable





# Words that carry no topic meaning on their own. A prompt made up ONLY of these words
# (plus the shared STOPWORDS) has nothing for the model to search on, so it is a genuine
# follow-up that should inherit the previous topic. A prompt containing ANY other word
# (e.g. "discovery", "negligence") always carries its own topic and must NOT be rewritten
# with the old chat's topic, even if it is short.








def sources_from_payload(payload: Any) -> List[SourceItem]:
    """Rebuild SourceItem objects from a saved assistant response payload."""
    out: List[SourceItem] = []
    if not isinstance(payload, dict):
        return out
    for raw in (payload.get("documents") or []) + (payload.get("source_badges") or []):
        if not isinstance(raw, dict):
            continue
        title = clean_display_title(str(raw.get("title") or "Source"))
        out.append(SourceItem(
            id=str(raw.get("id") or f"S{len(out)+1}"),
            title=title,
            excerpt=str(raw.get("excerpt") or ""),
            reason=str(raw.get("reason") or "Previously used source"),
            kind=str(raw.get("kind") or "source"),
            open_url=str(raw.get("open_url") or ""),
            download_url=str(raw.get("download_url") or ""),
            pages=str(raw.get("pages") or ""),
            colour=str(raw.get("colour") or SOURCE_COLOURS[len(out) % len(SOURCE_COLOURS)]),
            score=raw.get("score"),
            can_open=bool(raw.get("can_open")),
            download_name=safe_title(str(raw.get("download_name") or title)),
            source_uri_token=str(raw.get("source_uri_token") or ""),
        ))
    return unique_sources(out, limit=12)

















def _snippet(text: str, length: int = 520) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return cleaned[:length].strip()


@tool


def _search_knowledge_base(query: str, source_type: str = "all", limit: int = 8) -> List[SourceItem]:
    if not query.strip() or not kb_id():
        return []
    try:
        import boto3
        client = boto3.client("bedrock-agent-runtime", region_name=aws_region())
        vector_config: Dict[str, Any] = {"numberOfResults": max(1, min(int(limit or 8), 20))}
        if source_type in {"constitution", "statute", "case_law", "study_note"}:
            vector_config["filter"] = {"equals": {"key": "source_type", "value": source_type}}
        try:
            response = client.retrieve(
                knowledgeBaseId=kb_id(),
                retrievalQuery={"text": query},
                retrievalConfiguration={"vectorSearchConfiguration": vector_config},
            )
        except Exception:
            vector_config.pop("filter", None)
            response = client.retrieve(
                knowledgeBaseId=kb_id(),
                retrievalQuery={"text": query},
                retrievalConfiguration={"vectorSearchConfiguration": vector_config},
            )
    except Exception as exc:
        return [SourceItem(id="KB-ERROR", title="Knowledge base unavailable", reason=str(exc), kind="error", colour="rose")]

    output: List[SourceItem] = []
    for idx, item in enumerate(response.get("retrievalResults", [])[:limit], start=1):
        content = (item.get("content") or {}).get("text", "") or ""
        if not content.strip():
            continue
        location = item.get("location") or {}
        metadata = item.get("metadata") or {}
        s3_uri = (location.get("s3Location") or {}).get("uri", "")
        raw_title = (
            metadata.get("title")
            or metadata.get("document_title")
            or metadata.get("file_name")
            or metadata.get("source")
            or (s3_uri.split("/")[-1] if s3_uri else f"Knowledge source {idx}")
        )
        display = clean_display_title(str(raw_title))
        page = metadata.get("page") or metadata.get("page_number") or metadata.get("section") or metadata.get("chapter") or ""
        kind = metadata.get("source_type") or metadata.get("type") or source_type or "knowledge base"
        token = sign_kb_s3_source(s3_uri, str(raw_title))
        output.append(SourceItem(
            id=f"K{idx}",
            title=display,
            excerpt=_snippet(content, 900),
            reason="Relevant library source",
            kind=str(kind).replace("_", " "),
            pages=str(page) if page else "",
            colour=SOURCE_COLOURS[(idx - 1) % len(SOURCE_COLOURS)],
            score=item.get("score"),
            can_open=bool(token),
            open_url=f"/api/students/kb-sources/{token}/view/" if token else "",
            download_url=f"/api/students/kb-sources/{token}/download/" if token else "",
            download_name=safe_title(str(raw_title)),
            source_uri_token=token,
        ))
    return output


@tool


def _search_uploaded_documents(user_id: int, query: str, limit: int = 8) -> List[SourceItem]:
    from .models import StudentDocument

    terms = keywords_for_query(query)
    docs = StudentDocument.objects.filter(user_id=user_id, active=True).order_by("-updated_at")[:200]
    scored: List[Tuple[int, StudentDocument]] = []
    for doc in docs:
        title = (doc.title or "").lower()
        haystack = f"{doc.title}\n{(doc.extracted_text or '')[:80000]}".lower()
        score = 0
        for term in terms:
            if term in title:
                score += 8
            if term in haystack:
                score += 2
        if score > 0 or (not terms and query.strip()):
            scored.append((score, doc))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    output: List[SourceItem] = []
    for idx, (score, doc) in enumerate(scored[:limit], start=1):
        excerpt = _snippet(doc.extracted_text or "Stored study document. Open it from LAFRE to review the full file.", 620)
        output.append(SourceItem(
            id=f"D{doc.id}",
            title=clean_display_title(doc.title),
            excerpt=excerpt,
            reason="Relevant uploaded study material" if score else "Recent uploaded study document",
            kind="uploaded document",
            open_url=f"/api/students/documents/{doc.id}/view/",
            download_url=f"/api/students/documents/{doc.id}/download/",
            colour=SOURCE_COLOURS[(idx - 1) % len(SOURCE_COLOURS)],
            score=float(score),
            can_open=True,
            download_name=safe_title(doc.title),
        ))
    return output


@tool




















def unique_sources(*groups: List[SourceItem], limit: int = 12) -> List[SourceItem]:
    seen = set()
    output: List[SourceItem] = []
    for group in groups:
        for source in group:
            if source.kind == "error":
                continue
            key = (source.title.lower(), source.kind, source.pages)
            if key in seen:
                continue
            seen.add(key)
            output.append(source)
            if len(output) >= limit:
                return output
    return output


def generate_chat_title(question: str) -> str:
    """Create a short noun/action title for the recent chats sidebar."""
    cleaned = re.sub(r"\s+", " ", question or "").strip().strip("?.!")
    if not cleaned:
        return "New chat"
    sys = "Create short chat titles for a legal-study app. Return only the title."
    usr = f"""
Create a useful recent-chat title from this first student message:
{cleaned}

Rules:
- 2 to 6 words where possible.
- Prefer a noun phrase or action plus topic.
- No quotes.
- No full sentence.
- Do not write 'Chat about'.
Examples:
Explain section 17 and give me documents to study -> Section 17 study materials
Compare offer and invitation to treat -> Offer vs invitation to treat
Make flashcards on negligence -> Negligence flashcards
""".strip()
    generated = None
    if STRANDS_AVAILABLE:
        try:
            model_id = os.environ.get("BEDROCK_ROUTER_MODEL_ID") or os.environ.get("BEDROCK_FAST_MODEL_ID", "us.amazon.nova-micro-v1:0")
            model = BedrockModel(model_id=model_id, max_tokens=40, temperature=0.05)
            agent = Agent(name="LAFRETitleWriter", model=model, system_prompt=sys, callback_handler=None)
            result = agent(usr)
            generated = "".join(
                block.get("text", "") for block in getattr(result.message, "content", []) or [] if isinstance(block, dict)
            ).strip()
        except Exception:
            generated = None
    if generated:
        title = re.sub(r"[\n\r]+", " ", generated).strip().strip('"\'` .')
        title = re.sub(r"(?i)^title\s*:\s*", "", title).strip()
        words = title.split()
        if 1 <= len(words) <= 8:
            return title[:84]
    lowered = cleaned.lower()
    title = cleaned
    replacements = [
        (r"^(explain|discuss|define|describe)\s+", ""),
        (r"^(give me|show me|find)\s+(documents|sources|notes|materials)\s+(for|on|about)?\s*", ""),
        (r"^(make|create)\s+flashcards\s+(on|about|for)?\s*", ""),
        (r"^(turn|make)\s+.*\s+exam\s+answer\s*", "Exam answer"),
    ]
    for pattern, repl in replacements:
        title = re.sub(pattern, repl, title, flags=re.I).strip()
    if "compare" in lowered or " vs " in lowered or "versus" in lowered:
        title = re.sub(r"(?i)^compare\s+", "", cleaned).strip()
        title = title.replace(" and ", " vs ").replace(" versus ", " vs ")
    if "flashcard" in lowered and "flashcard" not in title.lower():
        title = f"{title} flashcards"
    words = title.split()
    if len(words) > 7:
        title = " ".join(words[:7])
    return title[:84] or "New chat"


def legal_information_notice() -> str:
    return DISCLAIMER_STUDENT


