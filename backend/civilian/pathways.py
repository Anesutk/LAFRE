from __future__ import annotations

FALLBACK_PATHWAYS = [
    {
        "id": "property_taken",
        "letter": "P",
        "group": "Property",
        "title": "Property taken",
        "short_description": "Belongings were taken, locked away or kept by another person.",
        "detailed_description": "Use this when a landlord, employer, relative, neighbour or other person has taken or refused to return your belongings. LAFRE will ask who took the property, whether there were threats or force, what proof you have, and whether police or document support may be needed.",
        "subtitle": "Belongings were taken, locked away or kept by another person.",
        "kb_terms": ["Zimbabwe property taken landlord belongings police report", "Zimbabwe return of property demand letter theft threats"],
        "background_routing_prompt": "property recovery belongings taken kept landlord employer police demand letter evidence",
        "urgency_keywords": ["threat", "violence", "assault", "force", "stolen", "theft"],
    },
    {
        "id": "eviction_lockout",
        "letter": "E",
        "group": "Housing",
        "title": "Eviction or lockout",
        "short_description": "You were told to leave, locked out, or threatened with removal.",
        "detailed_description": "Use this for eviction notices, rent disputes, changed locks, removed belongings or being forced out of a room, house or stand. LAFRE will check whether there is a lease, notice, court order, threats, removed property or urgent safety issue.",
        "subtitle": "You were told to leave, locked out, or threatened with removal.",
        "kb_terms": ["Zimbabwe eviction tenant landlord court order lockout", "Zimbabwe tenancy rights eviction notice lock changed"],
        "background_routing_prompt": "eviction lockout tenant landlord notice court order rent locks changed property removed",
        "urgency_keywords": ["locked out", "threat", "force", "violence", "assault"],
    },
    {
        "id": "money_owed",
        "letter": "M",
        "group": "Money",
        "title": "Money owed",
        "short_description": "Someone has not repaid money, salary, rent, invoice or a debt.",
        "detailed_description": "Use this when another person, customer, employer, tenant or business has failed to pay money. LAFRE will ask what agreement exists, amount owed, proof of payment/loan/work, messages, witnesses and whether a demand letter or review is needed.",
        "subtitle": "Someone has not repaid money, salary, rent, invoice or a debt.",
        "kb_terms": ["Zimbabwe debt recovery demand letter civil claim", "Zimbabwe unpaid money loan repayment evidence"],
        "background_routing_prompt": "debt recovery money owed demand letter civil claim loan salary rent invoice evidence",
    },
    {
        "id": "work_problem",
        "letter": "W",
        "group": "Work",
        "title": "Work problem",
        "short_description": "Unpaid salary, dismissal, suspension, contract or workplace treatment.",
        "detailed_description": "Use this for unpaid wages, dismissal, suspension, contract problems, benefits, workplace treatment or employer disputes. LAFRE will ask about employment status, dates, payslips, contract, messages and whether labour or lawyer review may be needed.",
        "subtitle": "Unpaid salary, dismissal, suspension, contract or workplace treatment.",
        "kb_terms": ["Zimbabwe labour unpaid salary dismissal employment contract", "Labour Act Zimbabwe wages dismissal dispute"],
        "background_routing_prompt": "labour employment salary dismissal suspension contract workplace dispute wages evidence",
    },
    {
        "id": "family_matter",
        "letter": "F",
        "group": "Family",
        "title": "Family matter",
        "short_description": "Maintenance, custody, divorce, access or family conflict.",
        "detailed_description": "Use this for child maintenance, custody, access, divorce, guardianship or family disputes. LAFRE will ask who is involved, children affected, court papers, urgency, safety and whether family court or lawyer support is needed.",
        "subtitle": "Maintenance, custody, divorce, access or family conflict.",
        "kb_terms": ["Zimbabwe maintenance custody divorce family law", "children maintenance court Zimbabwe custody access"],
        "background_routing_prompt": "family law maintenance custody divorce children access court safety lawyer review",
        "urgency_keywords": ["violence", "threat", "abuse", "injury", "assault"],
    },
    {
        "id": "business_at_home",
        "letter": "B",
        "group": "Business",
        "title": "Business at home",
        "short_description": "You want to run a small business from home or residence.",
        "detailed_description": "Use this for home shops, salons, food preparation, storage, customers visiting or small business activities from a house. LAFRE will ask about the activity, neighbours, health/safety risk, council rules, ownership or tenancy and whether local authority guidance is needed.",
        "subtitle": "You want to run a small business from home or residence.",
        "kb_terms": ["Zimbabwe home business council permit health by laws", "Zimbabwe local authority business licence home enterprise"],
        "background_routing_prompt": "home business council permit local authority health by laws customers food storage residence",
        "requires_location": True,
    },
    {
        "id": "land_or_well",
        "letter": "L",
        "group": "Land",
        "title": "Land or well issue",
        "short_description": "Land use, boundaries, borehole, well, neighbours or local office issue.",
        "detailed_description": "Use this for boundary disputes, boreholes, wells, land use, title issues, neighbours or local authority/community office problems. LAFRE will ask location, ownership proof, neighbours involved, permits and whether a council or community office route may be needed.",
        "subtitle": "Land use, boundaries, borehole, well, neighbours or local office issue.",
        "kb_terms": ["Zimbabwe borehole well permit land use council environmental health", "Zimbabwe land dispute boundary title deed property"],
        "background_routing_prompt": "land dispute well borehole boundary council community office title deed permit neighbour",
        "requires_location": True,
    },
    {
        "id": "other",
        "letter": "O",
        "group": "Other",
        "title": "My matter is different",
        "short_description": "Your issue does not fit the listed matter cards.",
        "detailed_description": "Use this if you are not sure which category fits. Describe what happened in your own words and LAFRE will ask follow-up questions before checking available legal resources.",
        "subtitle": "Your issue does not fit the listed matter cards.",
        "kb_terms": ["Zimbabwe legal procedure evidence rights"],
        "background_routing_prompt": "general legal issue classify matter Zimbabwe evidence support route",
    },
]

DEFAULT_QUESTIONS = [
    {"key": "issue", "label": "Briefly explain what happened", "type": "textarea"},
    {"key": "when", "label": "When did this happen?", "type": "text"},
    {"key": "city", "label": "City/town if local help may be needed", "type": "text"},
    {"key": "proof", "label": "What proof do you have?", "type": "multi", "options": ["Messages", "Photos", "Receipts", "Contract", "Witnesses", "Police report", "None yet"]},
    {"key": "danger", "label": "Is there any immediate danger, force, threat or injury?", "type": "single", "options": ["Yes", "No", "Not sure"]},
]

QUESTION_OVERRIDES = {
    "property_taken": [
        {"key": "who", "label": "Who took or kept the property?", "type": "single", "options": ["Landlord", "Employer", "Relative", "Neighbour", "Police", "Other"]},
        {"key": "items", "label": "Describe the items involved", "type": "textarea"},
        {"key": "danger", "label": "Was there force, threats, violence or injury?", "type": "single", "options": ["Yes", "No", "Not sure"]},
        {"key": "proof", "label": "What proof do you have?", "type": "multi", "options": ["Receipts", "Photos", "Messages", "Witnesses", "Agreement", "None yet"]},
        {"key": "city", "label": "City/town if police or support details may be needed", "type": "text"},
    ],
    "eviction_lockout": [
        {"key": "situation", "label": "Which situation applies?", "type": "single", "options": ["Received notice", "Locked out", "Rent dispute", "Property removed", "Court papers", "Other"]},
        {"key": "agreement", "label": "Do you have a lease or agreement?", "type": "single", "options": ["Yes", "No", "Not sure"]},
        {"key": "danger", "label": "Were threats, force or violence involved?", "type": "single", "options": ["Yes", "No", "Not sure"]},
        {"key": "city", "label": "City/town", "type": "text"},
    ],
}


def _db_pathways():
    try:
        from .models import PublicMatterType
        items = list(PublicMatterType.objects.filter(active=True).order_by("sort_order", "title"))
        return [item.to_public_dict() for item in items], {item.key: item.to_internal_dict() for item in items}
    except Exception:
        return [], {}


def list_pathways():
    items, _internal = _db_pathways()
    return items or FALLBACK_PATHWAYS


def get_pathway(pathway_id):
    _items, internal = _db_pathways()
    if pathway_id in internal:
        return internal[pathway_id]
    return next((p for p in FALLBACK_PATHWAYS if p["id"] == pathway_id), None)


def get_questions(pathway_id):
    p = get_pathway(pathway_id)
    if p and p.get("intake_questions"):
        return p["intake_questions"]
    return QUESTION_OVERRIDES.get(pathway_id) or DEFAULT_QUESTIONS
