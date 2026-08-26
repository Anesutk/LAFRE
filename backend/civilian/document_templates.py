from datetime import date

REVIEW_OPTIONS = [
    {"id": "review_only", "title": "Review only", "description": "A lawyer/reviewer checks wording and gives comments."},
    {"id": "stamp_only", "title": "Stamp / commission only", "description": "Use when the document needs commissioning/stamp guidance."},
    {"id": "sign_only", "title": "Sign only", "description": "Use when a lawyer/authorised reviewer must sign where appropriate."},
    {"id": "stamp_and_sign", "title": "Stamp + sign", "description": "Use when both stamp/commissioning and signature support are requested."},
]

TEMPLATES = {
    "affidavit_residence": {
        "title": "Affidavit of residence",
        "description": "For proof of residence. This is a draft; official use may require proper commissioning.",
        "kb_query": "Zimbabwe affidavit residence proof of residence commissioner of oaths template",
        "fields": ["full_name", "residence_address", "period_lived", "purpose", "city", "supporting_fact"],
    },
    "demand_letter": {
        "title": "Demand letter for money owed",
        "description": "For debt, unpaid invoice, or repayment demand.",
        "kb_query": "Zimbabwe demand letter debt money owed template civil claim",
        "fields": ["sender_name", "sender_address", "recipient_name", "amount", "reason", "proof", "deadline"],
    },
    "property_return_letter": {
        "title": "Letter demanding return of property",
        "description": "For property taken, kept, removed, or locked away.",
        "kb_query": "Zimbabwe letter demand return property landlord tenant property taken template",
        "fields": ["sender_name", "sender_address", "recipient_name", "property_list", "what_happened", "proof", "deadline"],
    },
    "police_report_summary": {
        "title": "Police report summary",
        "description": "Organise facts before reporting threats, theft, assault, or property taken.",
        "kb_query": "Zimbabwe police report assault threats theft property taken statement template",
        "fields": ["reporter_name", "contact", "incident_date", "incident_place", "incident_summary", "people_involved", "witnesses"],
    },
    "lawyer_consultation_brief": {
        "title": "Lawyer consultation brief",
        "description": "Prepare a short structured brief for lawyer/admin review.",
        "kb_query": "Zimbabwe lawyer consultation brief legal matter facts documents template",
        "fields": ["client_name", "contact", "issue", "facts", "documents", "questions_for_lawyer"],
    },
}

LABELS = {
    "full_name": "Full name", "residence_address": "Residence address", "period_lived": "How long you have lived there", "purpose": "Purpose / institution requesting proof", "city": "City/town", "supporting_fact": "Supporting fact or witness",
    "sender_name": "Your full name", "sender_address": "Your address", "recipient_name": "Recipient name", "amount": "Amount owed", "reason": "Why money is owed", "proof": "Proof you have", "deadline": "Deadline",
    "property_list": "List the property", "what_happened": "What happened", "reporter_name": "Reporter full name", "contact": "Phone/email", "incident_date": "Date/time", "incident_place": "Place", "incident_summary": "What happened", "people_involved": "People involved", "witnesses": "Witnesses", "client_name": "Client name", "issue": "Issue", "facts": "Facts", "documents": "Documents", "questions_for_lawyer": "Questions for lawyer",
}


def list_document_templates():
    return [{"id": k, "title": v["title"], "description": v["description"], "fields": v["fields"]} for k, v in TEMPLATES.items()]


def document_intake_payload(document_type, values=None):
    values = values or {}
    tpl = TEMPLATES.get(document_type) or TEMPLATES["lawyer_consultation_brief"]
    missing = [f for f in tpl["fields"] if not str(values.get(f, "")).strip()]
    if missing:
        return {
            "mode": "document_intake",
            "document_type": document_type,
            "title": tpl["title"],
            "description": tpl["description"],
            "fields": [{"key": f, "label": LABELS.get(f, f.replace("_", " ").title())} for f in missing],
            "review_options": REVIEW_OPTIONS,
        }
    return {"mode": "document_preview", "document_type": document_type, "title": tpl["title"], "content": generate_document(document_type, values), "review_options": REVIEW_OPTIONS}


def generate_document(document_type, v):
    today = date.today().strftime("%d %B %Y")
    if document_type == "affidavit_residence":
        return f"""AFFIDAVIT OF RESIDENCE

I, {v['full_name']}, residing at {v['residence_address']}, do hereby state as follows:

1. I am the person making this affidavit.
2. I currently reside at the above address.
3. I have lived at this address for {v['period_lived']}.
4. This affidavit is made for the purpose of {v['purpose']}.
5. {v.get('supporting_fact') or 'The facts stated above are true to the best of my knowledge.'}

Signed at {v.get('city') or '________________'} on this {today}.

____________________________
Signature of deponent

____________________________
Commissioner of Oaths / authorised person
"""
    if document_type == "property_return_letter":
        return f"""LETTER DEMANDING RETURN OF PROPERTY

From: {v['sender_name']}
Address: {v['sender_address']}
Date: {today}

To: {v['recipient_name']}

RE: DEMAND FOR RETURN OF PROPERTY

I write to request the return of the following property:
{v['property_list']}

What happened:
{v['what_happened']}

Proof available:
{v['proof']}

Please return the property by {v['deadline']}. If the property is not returned, I may seek further assistance including admin/lawyer review or lawful reporting where appropriate.

Yours faithfully,
{v['sender_name']}
"""
    if document_type == "demand_letter":
        return f"""DEMAND LETTER FOR MONEY OWED

From: {v['sender_name']}
Address: {v['sender_address']}
Date: {today}

To: {v['recipient_name']}

RE: DEMAND FOR PAYMENT OF {v['amount']}

I write to demand payment of {v['amount']}.

Reason the money is owed:
{v['reason']}

Proof available:
{v['proof']}

Please make payment by {v['deadline']}. If payment is not made, I may seek further lawful assistance.

Yours faithfully,
{v['sender_name']}
"""
    return "\n".join([f"{tpl}: {v.get(tpl, '')}" for tpl in TEMPLATES.get(document_type, TEMPLATES['lawyer_consultation_brief'])['fields']])
