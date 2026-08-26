from __future__ import annotations

import os
from typing import Dict, List

from django.db.models import Q

from .models import KnowledgeBaseNote

DEFAULT_LENDING_NOTES = [
    {
        "title": "Legal information notice",
        "body": "The platform should provide legal information and document support only. Legal advice, certification, stamping, representation and final review should be handled by a legal practitioner or authorised person where required.",
        "tags": ["notice", "legal information", "practitioner"],
    },
    {
        "title": "Loan agreement signing",
        "body": "A loan agreement should clearly identify the lender and borrower, amount, repayment terms, interest if any, default terms if any, security/collateral if any, date, signatures and witnesses where required.",
        "tags": ["loan", "agreement", "signature", "witness"],
    },
    {
        "title": "Interest and penalty caution",
        "body": "Interest, default penalty and collateral clauses may affect the legal position of the parties. The application should recommend legal-practitioner review when these terms are added.",
        "tags": ["interest", "penalty", "collateral", "review"],
    },
    {
        "title": "Proof and evidence",
        "body": "Users should keep the signed agreement, borrower identity details, proof that money was given, communication records and repayment receipts in the matter file.",
        "tags": ["proof", "receipt", "identity", "repayment"],
    },
]


def _external_bedrock_retrieve(query: str) -> List[Dict]:
    """Retrieve-only KB lookup. It does not call retrieve_and_generate and avoids high-cost generation."""
    kb_id = os.getenv("BEDROCK_KB_ID") or os.getenv("LAFRE_BEDROCK_KB_ID")
    region = os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION") or "us-east-1"
    if not kb_id:
        return []
    try:
        import boto3
        client = boto3.client("bedrock-agent-runtime", region_name=region)
        response = client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 6}},
        )
        results = []
        for item in response.get("retrievalResults", []):
            text = item.get("content", {}).get("text", "")
            loc = item.get("location", {}).get("s3Location", {}).get("uri", "")
            if text:
                results.append({"title": loc.split("/")[-1] if loc else "Knowledge base document", "body": text[:900], "source": loc, "kind": "external"})
        return results
    except Exception as exc:
        return [{"title": "Knowledge base retrieval error", "body": str(exc), "kind": "error"}]


def search_lending_kb(form: dict) -> Dict:
    borrower = (form.get("borrower") or {}).get("full_name", "borrower")
    loan = form.get("loan") or {}
    interest = form.get("interest") or {}
    security = form.get("security") or {}
    query = "loan agreement lending money repayment interest default collateral signatures witnesses legal information document validation"
    if interest.get("type") != "none":
        query += " interest rate practitioner review"
    if security.get("type") != "none":
        query += " security collateral legal review"

    q = Q(active=True) & (Q(matter_type="lending_money") | Q(matter_type=""))
    local_notes = list(KnowledgeBaseNote.objects.filter(q).filter(
        Q(title__icontains="loan") | Q(body__icontains="loan") | Q(tags__icontains="loan") | Q(tags__icontains="interest") | Q(tags__icontains="collateral")
    )[:8])
    local = [{"title": n.title, "body": n.body, "tags": n.tags, "kind": "local"} for n in local_notes]
    external = _external_bedrock_retrieve(query)
    fallback = DEFAULT_LENDING_NOTES if not local and not external else []
    items = local + external + fallback

    warnings = []
    if interest.get("type") != "none":
        warnings.append("Interest has been added. The term should be reviewed before the document is used.")
    if security.get("type") != "none":
        warnings.append("Security/collateral has been added. The wording should be reviewed before use.")
    if not (form.get("identity") or {}).get("borrower_id_number"):
        warnings.append("Borrower ID number is missing. The matter can continue but the document should leave space for it.")
    return {"used": True, "query": query, "items": items, "warnings": warnings, "borrower": borrower, "loan_amount": loan.get("amount")}
