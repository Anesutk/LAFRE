from __future__ import annotations

import re
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree as ET

from .knowledge_base import search_lending_kb
from .models import PathwayDocumentTemplate

LEGAL_NOTICE = (
    "Legal information only. This platform provides legal information and document support. "
    "Legal advice, certification, representation and final legal review should be handled by a legal practitioner where required."
)


def value(data: Dict, *keys: str, default: str = "") -> str:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
    return "" if cur is None else str(cur).strip()


def money(amount: str | Decimal | int | float, currency: str = "USD") -> str:
    try:
        d = Decimal(str(amount).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return f"{currency} [amount]"
    if d == d.to_integral_value():
        return f"{currency} {int(d)}"
    return f"{currency} {d:.2f}"


def get_active_template(matter_type="lending_money", document_type="loan_agreement"):
    return PathwayDocumentTemplate.objects.filter(matter_type=matter_type, document_type=document_type, active=True).order_by("-version", "-updated_at").first()


def validate_lending_form(form: Dict) -> Dict:
    missing = []
    reasons = []
    warnings = []
    review_flags = []

    checks = [
        ("lender.full_name", value(form, "lender", "full_name"), "Lender full name"),
        ("lender.phone", value(form, "lender", "phone"), "Lender phone number"),
        ("borrower.full_name", value(form, "borrower", "full_name"), "Borrower full name"),
        ("borrower.phone", value(form, "borrower", "phone"), "Borrower phone number"),
        ("loan.amount", value(form, "loan", "amount"), "Loan amount"),
        ("loan.purpose", value(form, "loan", "purpose"), "Purpose of loan"),
        ("loan.agreement_date", value(form, "loan", "agreement_date"), "Agreement date"),
    ]
    for _, val, label in checks:
        if not val:
            missing.append(label)
    try:
        amount = Decimal(str(value(form, "loan", "amount") or "0"))
        if amount <= 0:
            reasons.append("Loan amount must be greater than zero.")
    except (InvalidOperation, ValueError):
        reasons.append("Loan amount must be a valid number.")

    plan = value(form, "repayment", "plan_type") or "instalments"
    if plan == "single" and not value(form, "repayment", "single_due_date"):
        missing.append("Single payment due date")
    if plan in {"instalments", "custom"}:
        rows = (form.get("repayment") or {}).get("instalments") or []
        if not rows and not value(form, "repayment", "first_due_date"):
            missing.append("First instalment due date")

    if not value(form, "identity", "borrower_id_number") and not value(form, "borrower", "id_number"):
        warnings.append("Borrower ID number is missing. The matter can continue, but ID proof should be collected if available.")

    if value(form, "interest", "type") not in {"", "none"}:
        review_flags.append("Interest has been added. The interest term should be reviewed before the document is used.")
    if value(form, "default_terms", "type") not in {"", "none"}:
        review_flags.append("A default or late-payment penalty has been added. The wording should be reviewed before use.")
    if value(form, "security", "type") not in {"", "none"}:
        review_flags.append("Security/collateral has been added. The collateral wording should be reviewed before use.")

    return {
        "can_proceed": not missing and not reasons,
        "missing": missing,
        "reasons": reasons,
        "warnings": warnings,
        "review_flags": review_flags,
        "needs_practitioner_review": bool(review_flags),
        "legal_notice": LEGAL_NOTICE,
    }


def repayment_rows(form: Dict) -> List[Dict]:
    repayment = form.get("repayment") or {}
    currency = value(form, "loan", "currency") or "USD"
    if repayment.get("plan_type") == "single":
        return [{"number": 1, "due_date": repayment.get("single_due_date") or "", "amount": value(form, "loan", "amount"), "currency": currency, "status": "expected"}]
    rows = repayment.get("instalments") or []
    out = []
    for idx, row in enumerate(rows, start=1):
        out.append({"number": idx, "due_date": row.get("due_date") or "", "amount": row.get("amount") or "", "currency": row.get("currency") or currency, "status": row.get("status") or "expected"})
    return out


def repayment_summary(form: Dict) -> str:
    rows = repayment_rows(form)
    if not rows:
        return "[repayment schedule to be completed]"
    if len(rows) == 1:
        return f"single payment of {money(rows[0]['amount'], rows[0]['currency'])} on or before {rows[0]['due_date'] or '[date]'}"
    bits = [f"{money(r['amount'], r['currency'])} due {r['due_date'] or '[date]'}" for r in rows]
    return "; ".join(bits)


def interest_text(form: Dict) -> str:
    i = form.get("interest") or {}
    t = i.get("type") or "none"
    if t == "none":
        return "No interest is included in this agreement."
    if t == "percentage":
        return f"Interest is proposed at {i.get('percentage_rate') or '[rate]'}% {i.get('frequency') or 'monthly'}. This term should be reviewed before use."
    if t == "fixed":
        return f"Fixed interest of {money(i.get('fixed_amount'), value(form, 'loan', 'currency') or 'USD')} is proposed. This term should be reviewed before use."
    return "Interest terms require review."


def default_text(form: Dict) -> str:
    d = form.get("default_terms") or {}
    t = d.get("type") or "none"
    if t == "none":
        return "No late-payment penalty is included in this agreement."
    if t == "fixed":
        return f"A fixed late-payment penalty of {money(d.get('fixed_penalty'), value(form, 'loan', 'currency') or 'USD')} is proposed. This term should be reviewed before use."
    if t == "percentage":
        return f"A late-payment penalty of {d.get('percentage_penalty') or '[rate]'}% {d.get('frequency') or 'weekly'} is proposed. This term should be reviewed before use."
    return "Default terms require review."


def security_text(form: Dict) -> str:
    s = form.get("security") or {}
    t = s.get("type") or "none"
    if t == "none":
        return "No security or collateral is included in this agreement."
    desc = s.get("asset_description") or "[asset/security description]"
    serial = s.get("serial_or_id") or "[serial/ID number]"
    return f"Security/collateral is proposed: {desc}, Serial/ID: {serial}. This term should be reviewed before use."


def context(form: Dict) -> Dict:
    currency = value(form, "loan", "currency") or "USD"
    return {
        "lender_name": value(form, "lender", "full_name") or "________________",
        "lender_id": value(form, "lender", "id_number") or "________________",
        "lender_phone": value(form, "lender", "phone") or "________________",
        "lender_address": value(form, "lender", "address") or "________________",
        "lender_nationality": value(form, "lender", "nationality") or "________________",
        "borrower_name": value(form, "borrower", "full_name") or "________________",
        "borrower_id": value(form, "identity", "borrower_id_number") or value(form, "borrower", "id_number") or "________________",
        "borrower_phone": value(form, "borrower", "phone") or "________________",
        "borrower_address": value(form, "borrower", "address") or "________________",
        "borrower_nationality": value(form, "borrower", "nationality") or "________________",
        "agreement_date": value(form, "loan", "agreement_date") or "________________",
        "loan_amount": money(value(form, "loan", "amount"), currency),
        "loan_purpose": value(form, "loan", "purpose") or "________________",
        "repayment_summary": repayment_summary(form),
        "interest_clause": interest_text(form),
        "default_clause": default_text(form),
        "security_clause": security_text(form),
        "governing_law": "Laws of Zimbabwe",
    }


def extract_template_text(template: PathwayDocumentTemplate | None) -> str:
    if not template or not template.template_file:
        return ""
    path = Path(template.template_file.path)
    if not path.exists():
        return ""
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".docx":
        try:
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml")
            root = ET.fromstring(xml)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for p in root.findall(".//w:p", ns):
                text = "".join(t.text or "" for t in p.findall(".//w:t", ns))
                if text.strip():
                    paragraphs.append(text.strip())
            return "\n".join(paragraphs)
        except Exception:
            return ""
    return ""


def fill_placeholders(text: str, ctx: Dict) -> str:
    if not text:
        return text
    out = text
    for key, val in ctx.items():
        for token in ("{{" + key + "}}", "{{ " + key + " }}"):
            out = out.replace(token, str(val))
    return out


def default_document(form: Dict) -> str:
    c = context(form)
    return f"""LOAN AGREEMENT
Made in terms of the Moneylending and Rates of Interest Act [Chapter 14:14]

DATE OF AGREEMENT
This Agreement is made on {c['agreement_date']}.

1. THE PARTIES

1.1 LENDER
Full Name: {c['lender_name']}
I.D No.: {c['lender_id']}
Phone: {c['lender_phone']}
Physical Address: {c['lender_address']}
Nationality: {c['lender_nationality']}

1.2 BORROWER
Full Name: {c['borrower_name']}
I.D No.: {c['borrower_id']}
Phone: {c['borrower_phone']}
Physical Address: {c['borrower_address']}
Nationality: {c['borrower_nationality']}

2. LOAN DETAILS
The Lender lends to the Borrower, and the Borrower acknowledges receipt of, the principal sum of {c['loan_amount']}.
Purpose of the loan: {c['loan_purpose']}.

3. REPAYMENT
The Borrower shall repay the loan as follows: {c['repayment_summary']}.
Payment may be made by cash, bank transfer, mobile money or another written method agreed by the parties.

4. INTEREST
{c['interest_clause']}

5. DEFAULT
{c['default_clause']}

6. SECURITY / COLLATERAL
{c['security_clause']}

7. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the {c['governing_law']}.

8. GENERAL
This is the entire agreement between the parties. Any changes must be in writing and signed by both parties.

SIGNED BY THE PARTIES
Date: ____________________

LENDER
Signed: ____________________

BORROWER
Signed: ____________________

IN THE PRESENCE OF WITNESSES:
1. Name: ____________________   ID: ____________________   Signature: ____________________
2. Name: ____________________   ID: ____________________   Signature: ____________________

{LEGAL_NOTICE}
"""


def render_document(form: Dict, template: PathwayDocumentTemplate | None) -> str:
    template_text = extract_template_text(template)
    if template_text and "{{" in template_text:
        return fill_placeholders(template_text, context(form))
    # If a template is uploaded but has no placeholders, keep its structure by using default filled document.
    # The admin support note remains attached to the smart page.
    return default_document(form)


def build_smart_page(matter) -> Dict:
    form = matter.intake_json or {}
    c = context(form)
    validation = matter.validation_json or {}
    kb = matter.kb_support_json or {}
    rows = repayment_rows(form)
    attachments = list(matter.attachments.all()) if hasattr(matter, "attachments") else []
    cats = {a.category for a in attachments}
    status_chips = [{"label": "Legal information only", "kind": "grey"}]
    status_chips.append({"label": "Signed document uploaded" if "signed_document" in cats else "Pending signature", "kind": "green" if "signed_document" in cats else "warm"})
    status_chips.append({"label": "Proof uploaded" if "proof_of_loan" in cats else "Proof needed", "kind": "green" if "proof_of_loan" in cats else "red"})

    reqs = [
        "Both parties should read and sign the completed agreement.",
        "Upload the signed agreement, certified copy or stamped copy where required.",
        "Upload proof that money was given, such as transfer receipt, bank proof, mobile money screenshot, cash receipt or written acknowledgement.",
        "Keep borrower identity information and witness details where available.",
    ]
    if matter.document_template and matter.document_template.support_note:
        reqs.insert(0, matter.document_template.support_note)
    for w in validation.get("review_flags", []) + kb.get("warnings", []):
        if w not in reqs:
            reqs.append(w)

    summary = [
        f"{c['lender_name']} is recorded as the lender and {c['borrower_name']} is recorded as the borrower.",
        f"The matter records a proposed loan of {c['loan_amount']} for {c['loan_purpose']}. The agreement date is {c['agreement_date']}.",
        f"The repayment arrangement is: {c['repayment_summary']}.",
        "This page stores the generated agreement, the final signed document, proof that money was given, borrower supporting documents and repayment evidence.",
    ]
    return {
        "matter_id": matter.id,
        "title": matter.title,
        "status": matter.status,
        "status_chips": status_chips,
        "legal_information_notice": LEGAL_NOTICE,
        "summary_paragraphs": summary,
        "detail_groups": [
            {"title": "People involved", "items": [{"label": "Lender", "value": c["lender_name"]}, {"label": "Borrower", "value": c["borrower_name"]}, {"label": "Borrower ID", "value": c["borrower_id"]}]},
            {"title": "Dates and repayment", "items": [{"label": "Agreement date", "value": c["agreement_date"]}, {"label": "Repayment", "value": c["repayment_summary"]}]},
            {"title": "Terms", "items": [{"label": "Interest", "value": c["interest_clause"]}, {"label": "Default", "value": c["default_clause"]}, {"label": "Security", "value": c["security_clause"]}]},
        ],
        "document": {"type": "loan_agreement", "content": matter.generated_document_text},
        "document_requirements": reqs,
        "upload_sections": [
            {"key": "signed_document", "title": "Signed / certified / stamped document goes here", "description": "Upload the final signed agreement or certified/stamped copy where required.", "kind": "green"},
            {"key": "proof_of_loan", "title": "Proof money was given", "description": "Upload transfer receipt, bank proof, mobile money screenshot, cash receipt or written acknowledgement.", "kind": "blue"},
            {"key": "borrower_id", "title": "Borrower supporting documents", "description": "Upload ID copy, proof of residence, witness page or identity support documents.", "kind": "warm"},
            {"key": "repayment_evidence", "title": "Payment evidence", "description": "Upload repayment receipts or screenshots as payments are made.", "kind": "purple"},
        ],
        "repayment_schedule": rows,
        "kb_support": kb,
        "attachments": [
            {"id": a.id, "title": a.title, "category": a.category, "file_url": f"/api/civilian/documents/attachments/{a.id}/view/" if a.file else "", "uploaded_at": a.uploaded_at.isoformat()} for a in attachments
        ],
    }


def prepare_lending_matter(form: Dict) -> Dict:
    validation = validate_lending_form(form)
    kb = search_lending_kb(form)
    template = get_active_template()
    document = render_document(form, template)
    borrower = value(form, "borrower", "full_name") or "Borrower"
    return {"validation": validation, "kb": kb, "template": template, "document": document, "title": f"Loan to {borrower}"}
