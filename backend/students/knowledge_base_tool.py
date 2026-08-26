import os
import json
import boto3
from typing import Dict, List, Any, Optional
from django.conf import settings

try:
    from strands import tool
except Exception:
    def tool(fn):
        return fn

BEDROCK_KB_ID = (
    os.getenv("BEDROCK_KB_ID")
    or os.getenv("AWS_KB_ID")
    or os.getenv("BEDROCK_KNOWLEDGE_BASE_ID")
    or os.getenv("AWS_BEDROCK_KB_ID")
    or getattr(settings, "AWS_KB_ID", "")
).strip()
BEDROCK_REGION = (os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION") or getattr(settings, "AWS_REGION", "us-east-1") or "us-east-1").strip()
DEFAULT_RESULTS = int(os.getenv("BEDROCK_KB_RESULTS", "8"))


def _client():
    return boto3.client("bedrock-agent-runtime", region_name=BEDROCK_REGION)


def _build_metadata_filter(source_type: str | None) -> Optional[Dict[str, Any]]:
    """
    Optional future metadata filter.

    This only works if your Bedrock Knowledge Base documents have metadata such as:
      { "source_type": "case_law" }
      { "source_type": "statute" }
      { "source_type": "constitution" }
      { "source_type": "study_note" }

    If your KB does not have metadata yet, this function returns None and normal search works.
    """
    if not source_type or source_type == "all":
        return None

    allowed = {"case_law", "case", "statute", "act", "constitution", "study_note", "textbook", "regulation"}
    cleaned = source_type.strip().lower()
    if cleaned not in allowed:
        return None

    aliases = {
        "case": "case_law",
        "act": "statute",
    }
    cleaned = aliases.get(cleaned, cleaned)

    return {"equals": {"key": "source_type", "value": cleaned}}


def retrieve_legal_sources(
    query: str,
    number_of_results: int = DEFAULT_RESULTS,
    source_type: str = "all",
) -> List[Dict[str, Any]]:
    """
    Low-level helper used by Strands tools.
    Returns structured source objects from Amazon Bedrock Knowledge Base.
    """
    if not query or not query.strip():
        return []
    if not BEDROCK_KB_ID:
        return []

    vector_config: Dict[str, Any] = {
        "numberOfResults": max(1, min(int(number_of_results or DEFAULT_RESULTS), 20))
    }
    metadata_filter = _build_metadata_filter(source_type)
    if metadata_filter:
        vector_config["filter"] = metadata_filter

    response = _client().retrieve(
        knowledgeBaseId=BEDROCK_KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": vector_config},
    )

    results: List[Dict[str, Any]] = []
    for idx, item in enumerate(response.get("retrievalResults", []), start=1):
        content = item.get("content", {}).get("text", "") or ""
        location = item.get("location", {}) or {}
        s3_uri = location.get("s3Location", {}).get("uri", "")
        metadata = item.get("metadata", {}) or {}
        score = item.get("score")

        title = (
            metadata.get("title")
            or metadata.get("document_title")
            or metadata.get("file_name")
            or (s3_uri.split("/")[-1] if s3_uri else f"Source {idx}")
        )

        page = (
            metadata.get("page")
            or metadata.get("page_number")
            or metadata.get("section")
            or metadata.get("chapter")
            or ""
        )

        doc_type = metadata.get("source_type") or metadata.get("type") or source_type or "legal_source"

        results.append(
            {
                "title": str(title),
                "summary": content[:900].strip(),
                "excerpt": content[:1500].strip(),
                "url": "",
                "s3_uri": "",
                "pages": str(page) if page else "",
                "source_type": str(doc_type),
                "score": score,
                "metadata": metadata,
            }
        )
    return results


def sources_to_citations(sources: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, str]]:
    citations = []
    seen = set()
    for source in sources[:limit]:
        url = ""
        label = source.get("title") or "Legal source"
        key = (label, url)
        if key in seen:
            continue
        seen.add(key)
        citations.append({"label": label, "url": ""})
    return citations


def compact_sources_for_prompt(sources: List[Dict[str, Any]], limit: int = 6) -> str:
    blocks = []
    for i, source in enumerate(sources[:limit], start=1):
        blocks.append(
            f"[{i}] {source.get('title', 'Source')}\n"
            f"Type: {source.get('source_type', '')}\n"
            f"Pages/section: {source.get('pages', '')}\n"
            f"Excerpt: {source.get('excerpt') or source.get('summary') or ''}\n"
            f"Source link: available through LAFRE clean document viewer when enabled."
        )
    return "\n\n".join(blocks)


@tool
def search_knowledge_base(query: str, source_type: str = "all", number_of_results: int = DEFAULT_RESULTS) -> str:
    """
    Search the Zimbabwe legal knowledge base and return structured legal sources.
    Use this when you need statutes, constitutional provisions, cases, textbooks, or legal documents.
    """
    try:
        sources = retrieve_legal_sources(query, number_of_results, source_type)
        return json.dumps({"sources": sources}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": f"Error searching knowledge base: {exc}"}, ensure_ascii=False)
