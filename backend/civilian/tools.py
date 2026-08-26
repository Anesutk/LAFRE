import json
import re
from typing import Dict, List, Tuple
from django.db.models import Q
from strands import tool

from .knowledge_base import retrieve_legal_sources
from .local_services import GENERAL_EMERGENCY, find_services
from .models import Lawyer, AdminReviewRequest


ISSUE_TO_AREA = {
    "eviction": "property", "rent": "property", "tenant": "property", "landlord": "property",
    "locked out": "property", "lockout": "property", "house": "property", "property": "property",
    "land": "property", "deeds": "property", "title deed": "property",
    "divorce": "family", "maintenance": "family", "custody": "family", "marriage": "family",
    "child": "family", "children": "family",
    "dismissal": "employment", "fired": "employment", "salary": "employment", "wages": "employment",
    "job": "employment", "work": "employment", "employer": "employment", "employee": "employment",
    "arrest": "criminal", "bail": "criminal", "police": "criminal", "assault": "criminal",
    "detained": "criminal", "stolen": "criminal", "theft": "criminal", "fraud": "criminal",
    "court": "civil", "summons": "civil", "sue": "civil", "sheriff": "civil", "judgment": "civil",
    "contract": "contracts", "agreement": "contracts", "breach": "contracts",
    "debt": "consumer", "loan": "consumer", "borrow": "consumer", "borrowed": "consumer",
    "owe": "consumer", "owed": "consumer", "money": "consumer", "repay": "consumer", "repayment": "consumer",
    "company": "business", "business": "business", "shop": "business", "market": "business", "licence": "business", "license": "business",
    "permit": "business", "zoning": "business", "council": "business", "well": "property", "borehole": "property", "land use": "property",
    "will": "estates", "estate": "estates", "inheritance": "estates",
}

AREA_LABELS = {
    "property": "Property / landlord issue",
    "family": "Family issue",
    "employment": "Employment issue",
    "criminal": "Police / criminal issue",
    "civil": "Civil court issue",
    "contracts": "Contract issue",
    "consumer": "Debt / consumer issue",
    "business": "Business / permit issue",
    "estates": "Will / estate issue",
    "general": "General legal issue",
}

AREA_ALIASES = {
    "property": ["property", "civil"],
    "family": ["family"],
    "employment": ["employment", "civil"],
    "criminal": ["criminal", "civil"],
    "civil": ["civil", "contracts", "property", "consumer"],
    "contracts": ["contracts", "civil", "business", "consumer"],
    "consumer": ["consumer", "contracts", "civil", "business"],
    "business": ["business", "contracts", "civil"],
    "estates": ["estates", "property", "civil"],
    "general": ["general", "civil", "contracts"],
}

URGENT_WORDS = [
    "arrest", "arrested", "police", "court papers", "summons", "eviction today",
    "tomorrow", "locked out", "lockout", "domestic violence", "threat", "threatened", "bail",
    "deadline", "sheriff", "warrant", "detained", "custody emergency", "assault",
    "beaten", "injured", "blood", "stab", "rape", "sexual", "abuse", "violence",
]
POLICE_WORDS = [
    "assault", "threat", "threatened", "domestic violence", "police", "arrest", "detained",
    "stolen", "theft", "fraud", "locked out", "lockout", "violence", "abuse", "weapon", "robbed", "taken", "took", "seized", "removed",
]
HEALTH_WORDS = [
    "injured", "injury", "bleeding", "blood", "hospital", "clinic", "assault", "beaten",
    "rape", "sexual", "poison", "stab", "pain", "wound", "pregnant", "medical",
]
DOCUMENT_WORDS = ["draft", "letter", "affidavit", "agreement", "contract", "complaint", "notice", "demand", "document", "write", "prepare", "summary"]
CERTIFY_WORDS = ["certify", "certified", "stamp", "stamped", "official", "commission", "commissioned", "notarise", "notarize", "file", "court filing", "submit", "lodge"]
LAWYER_WORDS = ["lawyer", "attorney", "legal practitioner", "consult", "consultation", "represent", "representation"]
LOCAL_HELP_WORDS = LAWYER_WORDS + ["nearest", "near me", "police station", "charge office", "hospital", "clinic", "healthcare"]

BROAD_GUIDE_PHRASES = [
    "please guide me step by step",
    "what can i do",
    "help me understand what to do",
    "not sure what type",
    "needs help",
    "ask me to choose",
    "choose the exact situation",
    "first guide",
]

SOURCE_STOP_TITLES = {
    "consumer": ["public finance management", "appropriation", "finance act"],
    "contracts": ["public finance management", "appropriation"],
    "property": ["public finance management", "appropriation", "finance act"],
}

GUIDANCE_TEMPLATES = {
    "consumer": {
        "title": "Debt recovery and proof of borrowing",
        "answer": (
            "For a debt or borrowed money issue, start by proving that the debt exists and that repayment was expected. "
            "Useful proof includes a written loan agreement, WhatsApp/SMS messages, bank transfer records, receipts, invoices, "
            "witness names, and a clear calculation of the amount still outstanding. Avoid threats or force. Put your demand in writing "
            "and keep a copy. If the other person disputes the debt, ignores you, or court papers are involved, get a lawyer to check the next step."
        ),
        "steps": [
            "Write down who borrowed or owes the money, the date, amount, repayment terms, and what has already been paid.",
            "Collect proof: agreement, messages, bank records, receipts, invoices, witnesses, and any repayment plan.",
            "Send a calm written demand or reminder asking for payment or a written repayment plan by a clear date.",
            "If they deny the debt, threaten you, or the amount is large, speak to a lawyer before filing or signing anything.",
        ],
        "options": ["Someone owes me money", "I owe money", "Draft a demand letter", "I received summons", "Find a lawyer"],
    },
    "contracts": {
        "title": "Contract or agreement problem",
        "answer": (
            "For a contract dispute, the key is to show what was agreed, what each side was supposed to do, and how the agreement was broken. "
            "Collect the signed contract if there is one, messages, invoices, delivery notes, payment records, and a timeline. Start with a written notice asking the other side to fix the problem. "
            "If the contract is high value or already in court, get a lawyer to review it."
        ),
        "steps": [
            "Identify the agreement: who agreed, what was promised, the price, dates, and duties.",
            "Collect proof of performance or breach: receipts, delivery notes, photos, messages, or witnesses.",
            "Send a written notice asking the other side to perform, pay, refund, or explain within a reasonable time.",
            "Do not sign a settlement or new agreement unless you understand its effect.",
        ],
        "options": ["A contract was broken", "Goods/services were not delivered", "I need a demand letter", "Someone owes me money", "Find a lawyer"],
    },
    "property": {
        "title": "Landlord, eviction, or property issue",
        "answer": (
            "For a landlord or eviction issue, keep proof of your right to stay or use the property, such as a lease, receipts, messages, and notices. "
            "If you have been locked out, threatened, or property has been taken by force, treat it as urgent and consider police/public safety help as well as legal help. "
            "Do not use force to regain access; record what happened and get advice quickly."
        ),
        "steps": [
            "Keep the lease, rent receipts, messages, eviction notice, and photos of what happened.",
            "Write a timeline: when notice was given, what was said, and whether you were locked out or threatened.",
            "If there is force, threats, or property taken, consider reporting at the nearest police station/charge office.",
            "If court papers or a deadline are involved, speak to a lawyer urgently.",
        ],
        "options": ["I received an eviction notice", "I was locked out", "My property was taken", "Rent dispute", "Find a lawyer"],
    },
    "employment": {
        "title": "Employment or unpaid salary problem",
        "answer": (
            "For an employment problem, collect proof of the job relationship and the problem. This can include your contract, payslips, messages, dismissal letter, work schedules, and bank records. "
            "Write a clear summary of what happened and when. If you were dismissed, unpaid, injured at work, or threatened, get advice before signing any settlement."
        ),
        "steps": [
            "Collect your contract, payslips, bank messages, dismissal letter, and workplace messages.",
            "Write the dates: when you started, what changed, when you were unpaid/dismissed, and who was involved.",
            "Ask for reasons or payment in writing so there is a record.",
            "If the employer refuses or there is a hearing/deadline, consult a labour lawyer or legal aid service.",
        ],
        "options": ["Unpaid salary", "Unfair dismissal", "No written contract", "Work injury", "Find a lawyer"],
    },
    "family": {
        "title": "Family law issue",
        "answer": (
            "For family matters like divorce, maintenance, custody, or guardianship, keep documents showing the relationship, children involved, payments, messages, and any previous orders. "
            "Because family matters can affect children and rights, it is usually safer to get lawyer or legal aid review before filing documents."
        ),
        "steps": [
            "Collect marriage documents, birth certificates, payment records, messages, and previous court papers.",
            "Write down what outcome you need: maintenance, custody, divorce, access, protection, or property division.",
            "Keep the child’s safety and welfare first where children are involved.",
            "For court papers or disputes over children, consult a lawyer or legal aid service.",
        ],
        "options": ["Maintenance", "Custody/access", "Divorce", "Domestic violence", "Find a lawyer"],
    },
    "criminal": {
        "title": "Police, arrest, or criminal issue",
        "answer": (
            "If police, arrest, threats, assault, or detention are involved, focus first on safety and accurate records. Write down the station, officer names if known, dates, charge or allegation, witnesses, and any injuries. "
            "For arrest, detention, bail, assault, or domestic violence, contact a lawyer or trusted person quickly. If there is injury, seek healthcare."
        ),
        "steps": [
            "Move to a safe place if there is immediate danger.",
            "Write down what happened, when, where, who was involved, and any officer/station details.",
            "Keep evidence: photos, medical report, messages, witness names, and police reference if available.",
            "Contact a lawyer, legal aid, or trusted person if arrest, detention, bail, or serious allegations are involved.",
        ],
        "options": ["I was assaulted", "Someone threatened me", "Someone was arrested", "I need bail help", "Find a lawyer"],
    },
    "civil": {
        "title": "Civil court or dispute issue",
        "answer": (
            "For civil disputes or court papers, keep every document and note the deadline. Court papers usually have time limits. Do not ignore summons, judgments, or sheriff notices. "
            "Prepare a short timeline and get legal advice quickly if you need to respond."
        ),
        "steps": [
            "Keep the summons, notice, judgment, sheriff letter, or any court document.",
            "Check the dates and deadlines on the document.",
            "Write a timeline of the dispute and collect contracts, receipts, messages, and witnesses.",
            "Speak to a lawyer before missing a deadline or signing a settlement.",
        ],
        "options": ["I received summons", "Sheriff notice", "I want to sue", "I need to respond", "Find a lawyer"],
    },
    "business": {
        "title": "Business, licence, or permit issue",
        "answer": (
            "Before starting a business from home or changing how property is used, separate the legal risks: council/local authority permission, business or shop licensing, health and safety, nuisance to neighbours, traffic/noise/waste, and any lease or title-deed restrictions. Do not only ask whether the business is profitable; ask whether the property may lawfully be used that way and whether inspections or permits are needed first."
        ),
        "steps": [
            "Identify the exact activity: goods sold, services offered, food/chemicals handled, stock stored, machinery used, signage, employees, and customer visits.",
            "Check with the local authority/council before operating publicly, especially if customers will visit, food is handled, waste/noise is produced, or signage/stalls are used.",
            "If you rent, check your lease or ask the owner/landlord whether business use is allowed.",
            "Keep written proof of all enquiries, approvals, licence applications, inspections, and council responses.",
            "If neighbours object, council threatens enforcement, or a permit is refused, get legal advice before continuing or paying penalties.",
        ],
        "options": ["Start business at home", "Food or market business", "Council permit issue", "Neighbour complaint", "Draft council enquiry letter"],
    },
    "estates": {
        "title": "Estate, inheritance, or will issue",
        "answer": (
            "For inheritance or estate matters, collect the death certificate, will if available, family details, list of assets and debts, and any previous court or estate documents. "
            "Estate matters can become complex, so lawyer or admin review is recommended before drafting official papers."
        ),
        "steps": [
            "Collect the death certificate, will, family details, and list of assets/debts.",
            "Write down who is claiming what and whether there is a dispute.",
            "Keep any court, master’s office, or estate documents together.",
            "Get lawyer/legal aid review before signing or filing estate documents.",
        ],
        "options": ["There is a will", "No will", "Family dispute", "Property in estate", "Find a lawyer"],
    },
    "general": {
        "title": "General legal help",
        "answer": (
            "Start by writing a short timeline of what happened, collecting documents and messages, and identifying what help you need: explanation, letter, police/healthcare referral, lawyer, or admin review. "
            "If there is danger, injury, arrest, court papers, or a deadline, treat it as urgent."
        ),
        "steps": [
            "Write the main facts in date order.",
            "Collect notices, agreements, receipts, messages, photos, and witness names.",
            "Choose whether you need explanation, a document draft, lawyer referral, police/healthcare help, or admin review.",
        ],
        "options": ["Landlord issue", "Work problem", "Debt/contract", "Family issue", "Police/arrest", "Find a lawyer"],
    },
}

CITY_OPTIONS = ["Harare", "Bulawayo", "Gweru", "Mutare", "Masvingo", "Kwekwe", "Kadoma", "Chinhoyi", "Marondera", "Victoria Falls", "Other"]


def detect_practice_area(issue: str) -> str:
    issue = (issue or "").lower()
    for keyword, area in ISSUE_TO_AREA.items():
        if keyword in issue:
            return area
    return "general"


def is_urgent(issue: str) -> bool:
    issue = (issue or "").lower()
    return any(word in issue for word in URGENT_WORDS)


def wants_document(issue: str) -> bool:
    issue = (issue or "").lower()
    return any(word in issue for word in DOCUMENT_WORDS)


def wants_certification(issue: str) -> bool:
    issue = (issue or "").lower()
    return any(word in issue for word in CERTIFY_WORDS)


def wants_lawyer(issue: str) -> bool:
    issue = (issue or "").lower()
    return any(word in issue for word in LAWYER_WORDS)


def wants_local_help(issue: str) -> bool:
    issue = (issue or "").lower()
    return any(word in issue for word in LOCAL_HELP_WORDS)


def is_broad_category_prompt(issue: str) -> bool:
    lower = (issue or "").lower().strip()
    if len(lower.split()) > 22:
        # Longer messages usually contain enough facts to answer.
        return False
    return any(phrase in lower for phrase in BROAD_GUIDE_PHRASES)


def _checklist_for_area(area: str) -> List[str]:
    checklists = {
        "property": ["Lease agreement or proof of occupation", "Payment receipts or bank messages", "Eviction notice or messages from landlord", "Photos, videos, or witness names", "National ID and contact details"],
        "family": ["Marriage certificate or proof of relationship", "Children's birth certificates where relevant", "Messages, payment records, or agreements", "Any previous court papers or orders", "National ID and contact details"],
        "employment": ["Employment contract or offer letter", "Payslips, salary messages, or bank records", "Dismissal letter or disciplinary notice", "Workplace messages and witness names", "Timeline of what happened"],
        "criminal": ["Police station or officer details if known", "Charge or allegation if known", "Names of witnesses", "Photos, medical reports, or messages", "Contact details for family/emergency person"],
        "civil": ["Court papers, summons, notices, or sheriff letters", "Deadline dates appearing on the papers", "Contracts, receipts, messages, and photos", "Witness names and contact details", "Timeline of the dispute"],
        "contracts": ["Signed agreement or draft contract", "Payment proof and invoices", "Messages about the agreement", "Delivery notes or proof of performance", "Timeline of breach or dispute"],
        "consumer": ["Loan agreement, IOU, receipt, or invoice", "Bank transfer records or EcoCash/OneMoney messages", "WhatsApp/SMS messages showing borrowing or repayment terms", "Repayment plan or calculation of outstanding balance", "Demand letters received or sent"],
        "business": ["Company papers or registration documents", "Contracts, invoices, and receipts", "Messages with partners/customers", "Bank/payment records", "Summary of the dispute or transaction"],
        "estates": ["Death certificate", "Will if available", "List of assets and debts", "Family member details", "Previous estate or court papers"],
        "general": ["National ID", "Any written agreement or notice", "Receipts, messages, photos, or emails", "Names and contact details of people involved", "Short timeline of what happened"],
    }
    return checklists.get(area, checklists["general"])


def _source_query(issue: str, area: str) -> str:
    templates = {
        "consumer": f"Zimbabwe debt recovery loan repayment agreement proof of debt demand letter civil claim repayment plan {issue}",
        "contracts": f"Zimbabwe contract breach agreement payment proof demand letter civil claim {issue}",
        "property": f"Zimbabwe landlord tenant eviction lease rent lockout property rights {issue}",
        "employment": f"Zimbabwe labour employment unpaid salary dismissal contract wages {issue}",
        "family": f"Zimbabwe family law divorce maintenance custody children court {issue}",
        "criminal": f"Zimbabwe criminal procedure arrest bail assault police report rights {issue}",
        "civil": f"Zimbabwe civil procedure summons judgment sheriff debt claim court papers {issue}",
        "business": f"Zimbabwe business contract company dispute invoice payment {issue}",
        "estates": f"Zimbabwe estate inheritance will deceased estate property {issue}",
        "general": f"Zimbabwe legal rights civil procedure evidence documents {issue}",
    }
    return templates.get(area, templates["general"])


def _tokens(text: str) -> set:
    words = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
    noisy = {"zimbabwe", "legal", "court", "matter", "issue", "document", "documents", "chapter"}
    return {w for w in words if w not in noisy}


def clean_sources(sources: List[Dict], issue: str, area: str, limit: int = 3) -> List[Dict]:
    """Keep only source cards that look relevant enough for users to open."""
    if not sources:
        return []
    issue_tokens = _tokens(issue) | _tokens(_source_query(issue, area))
    stop_titles = SOURCE_STOP_TITLES.get(area, [])
    cleaned = []
    seen = set()
    for src in sources:
        title = (src.get("title") or "Legal source").strip()
        excerpt = (src.get("excerpt") or "").strip()
        url = ""
        title_lower = title.lower()
        if any(stop in title_lower for stop in stop_titles):
            continue
        key = (title_lower, url)
        if key in seen:
            continue
        seen.add(key)
        combined_tokens = _tokens(title + " " + excerpt)
        overlap = len(issue_tokens & combined_tokens)
        # Cases may still be useful if they mention repayment/debt/lease etc even without exact overlap.
        if overlap == 0 and area != "general":
            continue
        cleaned.append({
            "title": title,
            "excerpt": excerpt[:420],
            "url": "",
            "s3_uri": "",
            "score": src.get("score"),
            "relevance": "Open this if you want to verify the legal background used by the assistant.",
        })
        if len(cleaned) >= limit:
            break
    return cleaned


def get_relevant_sources(issue: str, area: str, limit: int = 3) -> List[Dict]:
    result = retrieve_legal_sources(query=_source_query(issue, area), number_of_results=8)
    if not result.get("ok"):
        return []
    return clean_sources(result.get("sources", []), issue=issue, area=area, limit=limit)



def sources_to_context(sources: List[Dict], max_chars: int = 3500) -> str:
    """Compact KB excerpts for the live agent. Not shown to civilian users."""
    if not sources:
        return "No close knowledge-base extract was retrieved. Do not invent specific law; give cautious practical preparation steps and recommend review if needed."
    chunks = []
    total = 0
    for idx, src in enumerate(sources[:5], 1):
        title = (src.get("title") or "Legal source").strip()
        excerpt = (src.get("excerpt") or "").strip().replace("\n", " ")
        if not excerpt:
            continue
        chunk = f"[Source {idx}] {title}\n{excerpt[:900]}"
        if total + len(chunk) > max_chars:
            break
        total += len(chunk)
        chunks.append(chunk)
    return "\n\n".join(chunks) if chunks else "No usable knowledge-base extract was retrieved."


def fallback_detailed_guidance(issue: str, city: str = "", sources: List[Dict] | None = None, include_lawyers: bool = False) -> Dict:
    """Safer detailed fallback when the live model fails or gives a poor answer."""
    area = detect_practice_area(issue)
    template = GUIDANCE_TEMPLATES.get(area, GUIDANCE_TEMPLATES["general"])
    lower = (issue or "").lower()
    urgent = is_urgent(issue)
    payload = build_public_guidance_payload(issue, city, include_lawyers=include_lawyers, include_sources=False)
    payload["title"] = template["title"]
    payload["mode"] = "urgent_help" if urgent else "legal_guidance"
    payload["plain_language_answer"] = template["answer"]
    payload["important_points"] = []
    if area == "property":
        payload["important_points"] = [
            "Do not use force to recover access or property; record what happened and use lawful channels.",
            "If property was taken, locked away, damaged, or removed by force, keep a list of the items and proof that they belong to you.",
            "If threats, violence, theft, or forced lockout are involved, police/public-safety help may be appropriate as well as legal help.",
            "If there are court papers, deadlines, or eviction notices, treat the matter as urgent and get legal review quickly.",
        ]
        payload["procedures"] = [
            "Write a timeline: date, place, who took the property, what was said, and witnesses.",
            "Make an inventory of the property taken, with estimated value and any receipts/photos proving ownership.",
            "Keep lease/rent proof and messages showing your right to occupy or keep the property there.",
            "If force, threats, breaking-in, or theft is alleged, consider reporting at the nearest police station/charge office and ask for a reference number.",
            "If the dispute is mainly landlord-tenant or civil recovery, prepare the facts for a lawyer or legal aid office before filing anything.",
        ]
    elif area == "consumer":
        payload["important_points"] = [
            "Debt recovery depends heavily on proof that the debt exists and the amount is correctly calculated.",
            "Messages, receipts, bank transfers, invoices, IOUs, and repayment plans are often more useful than verbal claims alone.",
            "Avoid threats or taking property by force; use written demand, negotiation, or lawful court/legal processes.",
        ]
        payload["procedures"] = [
            "Write the lender/borrower names, amount, date, repayment terms, payments made, and current balance.",
            "Collect proof of borrowing and proof of non-payment.",
            "Send a written demand requesting payment or a repayment proposal by a clear date.",
            "If the debtor denies the debt, the amount is high, or court papers are involved, consult a lawyer before proceeding.",
        ]
    elif area == "employment":
        payload["important_points"] = [
            "Your proof should show the employment relationship and the exact problem: unpaid wages, dismissal, injury, or disciplinary issue.",
            "Keep written records before meetings or settlements.",
        ]
    elif area == "criminal":
        payload["important_points"] = [
            "Safety comes first. If there is danger or injury, seek police/healthcare help immediately.",
            "Keep names, dates, station details, witnesses, photos, medical reports, and police reference numbers.",
        ]
    else:
        payload["important_points"] = [
            "The strongest next step is to organise the facts, documents, dates, and proof before choosing a legal route.",
            "If deadlines, court papers, danger, or official documents are involved, get human legal review.",
        ]
    payload["proof_items"] = _checklist_for_area(area)
    payload.pop("checklist", None)
    if sources:
        payload["used_knowledge_base"] = True
        payload["source_count"] = len(sources)
    else:
        payload["used_knowledge_base"] = False
        payload["source_count"] = 0
        payload["needs_review"] = True
        payload.setdefault("missing_information", []).append("No close knowledge-base extract was found for this exact issue.")
    return payload


def _apply_lawyer_query(qs, aliases: List[str]):
    query = Q()
    for alias in aliases:
        query |= Q(practice_areas__icontains=alias) | Q(services__icontains=alias)
    return qs.filter(query)


def lawyers_payload(issue: str, city: str = "", limit: int = 4) -> dict:
    area = detect_practice_area(issue)
    aliases = AREA_ALIASES.get(area, [area])
    base = Lawyer.objects.filter(is_active=True, available_for_appointments=True)
    area_qs = _apply_lawyer_query(base, aliases)

    match_note = "Matched by legal issue."
    qs = area_qs
    if city:
        city_area_qs = area_qs.filter(city__icontains=city)
        if city_area_qs.exists():
            qs = city_area_qs
            match_note = "Matched by city and legal issue."
        elif area_qs.exists():
            qs = area_qs
            match_note = "No exact city match was found, so showing issue-matched lawyers from the demo database."
        else:
            qs = base.filter(city__icontains=city)
            match_note = "No exact issue match was found, so showing lawyers in the selected city from the demo database."
    elif not area_qs.exists():
        qs = base
        match_note = "No exact issue match was found, so showing available demo lawyers."

    lawyers = qs.order_by("-verified", "-rating", "-review_count", "full_name")[: max(1, min(limit, 10))]
    return {
        "mode": "lawyer_referral",
        "detected_area": area,
        "city": city,
        "lawyers": [
            {
                "id": lawyer.id,
                "full_name": lawyer.full_name,
                "firm_name": lawyer.firm_name,
                "slug": lawyer.slug,
                "city": lawyer.city,
                "province": lawyer.province,
                "practice_areas": lawyer.practice_areas,
                "services": lawyer.services,
                "rating": str(lawyer.rating),
                "review_count": lawyer.review_count,
                "years_experience": lawyer.years_experience,
                "consultation_mode": lawyer.consultation_mode,
                "consultation_fee_usd": str(lawyer.consultation_fee_usd) if lawyer.consultation_fee_usd is not None else None,
                "verified": lawyer.verified,
                "phone": lawyer.phone,
                "email": lawyer.email,
                "bio": lawyer.bio,
            }
            for lawyer in lawyers
        ],
        "notice": "Prototype lawyer recommendations from dummy/platform data.",
        "match_note": match_note,
    }


def build_guided_options_payload(issue: str, city: str = "") -> Dict:
    area = detect_practice_area(issue)
    template = GUIDANCE_TEMPLATES.get(area, GUIDANCE_TEMPLATES["general"])
    return {
        "mode": "guided_options",
        "title": f"Let us narrow this {AREA_LABELS.get(area, 'legal issue').lower()}",
        "urgency": "High" if is_urgent(issue) else "Normal",
        "issue_type": area,
        "plain_language_answer": template["answer"],
        "next_steps": template["steps"][:2],
        "proof_items": _checklist_for_area(area),
        "options": template["options"],
        "city": city,
    }


def build_needs_city_payload(issue: str, city: str = "") -> Dict:
    area = detect_practice_area(issue)
    return {
        "mode": "needs_city",
        "title": "Which city should I use?",
        "urgency": "Normal",
        "issue_type": area,
        "plain_language_answer": "I can give general guidance without your city. I only need the city for nearby lawyer, police, or healthcare suggestions.",
        "options": CITY_OPTIONS,
        "cities": CITY_OPTIONS,
    }


def build_public_guidance_payload(issue: str, city: str = "", include_lawyers: bool = False, include_sources: bool = True) -> Dict:
    area = detect_practice_area(issue)
    template = GUIDANCE_TEMPLATES.get(area, GUIDANCE_TEMPLATES["general"])
    urgent = is_urgent(issue)
    lower = (issue or "").lower()
    local_services = []
    healthcare = []
    general_emergency = None

    if any(word in lower for word in POLICE_WORDS):
        local_services = find_services(city=city, service_type="police")
        general_emergency = GENERAL_EMERGENCY
    if any(word in lower for word in HEALTH_WORDS):
        healthcare = find_services(city=city, service_type="healthcare")
        general_emergency = GENERAL_EMERGENCY

    sources = get_relevant_sources(issue, area, limit=3) if include_sources else []
    lawyers = []
    lawyer_note = ""
    if include_lawyers and (city or wants_lawyer(issue) or urgent):
        lawyer_data = lawyers_payload(issue=issue, city=city, limit=4)
        lawyers = lawyer_data.get("lawyers", [])
        lawyer_note = lawyer_data.get("match_note", "")

    next_steps = list(template["steps"])
    if include_lawyers and not city and wants_lawyer(issue):
        next_steps.append("To recommend nearby lawyers, choose your city below or type your city.")
    elif include_lawyers and city and lawyers:
        next_steps.append("Review the lawyer cards below and contact one if you need personalised advice or representation.")

    payload = {
        "mode": "legal_guidance" if not urgent else "urgent_help",
        "title": template["title"],
        "urgency": "High" if urgent else "Normal",
        "issue_type": area,
        "plain_language_answer": template["answer"],
        "next_steps": next_steps,
        "proof_items": _checklist_for_area(area),
        "sources": sources,
        "recommended_lawyers": lawyers,
        "lawyer_note": lawyer_note,
        "local_services": local_services,
        "healthcare": healthcare,
        "general_emergency": general_emergency,
        "suggestions": template["options"] + (["Choose city for lawyer recommendation"] if include_lawyers and not city else []),
    }
    return payload


def response_has_dumped_details(text: str) -> bool:
    text = text or ""
    red_flags = ["Lawyer:", "Firm:", "Phone:", "Email:", "URL:", "Excerpt:", "Here are some legal sources", "Please note that this is a prototype"]
    return any(flag.lower() in text.lower() for flag in red_flags)


@tool
def classify_public_legal_issue(issue: str) -> str:
    """Classify a public user's legal issue into a broad area and urgency."""
    area = detect_practice_area(issue)
    urgent = is_urgent(issue)
    return json.dumps({
        "mode": "issue_classification",
        "issue_type": area,
        "label": AREA_LABELS.get(area, "General legal issue"),
        "urgency": "High" if urgent else "Normal",
        "needs_lawyer": urgent or wants_lawyer(issue) or area in ["criminal", "family", "property", "civil", "estates"],
        "needs_document": wants_document(issue),
        "needs_paid_service": wants_certification(issue),
        "needs_city_only_for_local_help": wants_local_help(issue),
    })


@tool
def ask_guided_follow_up(issue: str, city: str = "") -> str:
    """Return clickable guided options instead of asking the user to type everything manually."""
    return json.dumps(build_guided_options_payload(issue, city))


@tool
def assess_safety_and_referral(issue: str, city: str = "") -> str:
    """Assess whether the issue needs police, healthcare, lawyer, or urgent legal action."""
    lower = (issue or "").lower()
    needs_police = any(word in lower for word in POLICE_WORDS)
    needs_healthcare = any(word in lower for word in HEALTH_WORDS)
    urgent = is_urgent(issue) or needs_police or needs_healthcare
    area = detect_practice_area(issue)
    return json.dumps({
        "mode": "safety_referral",
        "risk_level": "High" if urgent else "Normal",
        "issue_type": area,
        "show_police_card": needs_police,
        "show_healthcare_card": needs_healthcare,
        "show_lawyer_cards": urgent or area in ["criminal", "family", "property", "civil"],
        "reason": "Safety, police, healthcare, or urgent legal help may be needed based on the user's message.",
        "city": city,
    })


@tool
def recommend_local_services(issue: str, city: str = "") -> str:
    """Recommend local police/charge-office or healthcare services."""
    lower = (issue or "").lower()
    services = []
    healthcare = []
    if any(word in lower for word in POLICE_WORDS) or "police" in lower or "charge office" in lower:
        services = find_services(city=city, service_type="police")
    if any(word in lower for word in HEALTH_WORDS) or "health" in lower or "clinic" in lower or "hospital" in lower:
        healthcare = find_services(city=city, service_type="healthcare")
    return json.dumps({
        "mode": "local_services",
        "service_type": "mixed" if services and healthcare else ("healthcare" if healthcare else "police"),
        "city": city,
        "general_emergency": GENERAL_EMERGENCY,
        "services": services,
        "healthcare": healthcare,
        "disclaimer": "Prototype service list. Confirm details before production.",
    })


@tool
def search_public_legal_sources(query: str, number_of_results: int = 5) -> str:
    """Search verified legal documents in the Bedrock Knowledge Base and return filtered source cards."""
    area = detect_practice_area(query)
    sources = get_relevant_sources(query, area, limit=number_of_results)
    return json.dumps({
        "mode": "source_results",
        "query": _source_query(query, area),
        "ok": True,
        "sources": sources,
        "source_count": len(sources),
        "note": "Sources are supporting references only; practical guidance should be written separately.",
    })


@tool
def create_evidence_checklist(issue: str) -> str:
    """Create a practical evidence/documents-to-collect checklist for a civilian issue."""
    area = detect_practice_area(issue)
    return json.dumps({
        "mode": "evidence_checklist",
        "title": "Documents and evidence to collect",
        "issue_type": area,
        "items": _checklist_for_area(area),
        "note": "These checkboxes are a to-do list for the user. They are not uploaded automatically.",
    })


@tool
def recommend_lawyers(issue: str, city: str = "", limit: int = 4) -> str:
    """Recommend lawyers from the platform database. Use as supporting cards, not as the whole answer."""
    return json.dumps(lawyers_payload(issue=issue, city=city, limit=limit))


@tool
def prepare_document_draft(issue: str, document_type: str = "letter", city: str = "") -> str:
    """Prepare a cautious first draft for simple documents only."""
    lower = (issue or "").lower()
    high_risk_doc = any(word in lower for word in ["affidavit", "court", "summons", "deed", "transfer", "custody", "criminal", "bail"])
    area = detect_practice_area(issue)
    sources = get_relevant_sources(f"{document_type} {issue}", area, limit=3)
    needs_review = high_risk_doc or len(sources) == 0
    if high_risk_doc:
        draft_title = "Facts summary for lawyer/admin review"
        body = (
            "FACTS SUMMARY\n\n"
            "I am requesting help with the following issue:\n"
            f"{issue}\n\n"
            "Timeline:\n1. [Add date and what happened]\n2. [Add date and what happened]\n3. [Add date and what happened]\n\n"
            "Documents available:\n- [List notices, receipts, messages, contracts, IDs, photos]\n\n"
            "Help needed:\n- Please review the facts and advise on the correct document or next step."
        )
    else:
        draft_title = "Draft letter"
        body = (
            "[Your name]\n[Your address]\n[Your phone]\n[Date]\n\n"
            "To: [Recipient name]\n\n"
            "RE: Request to resolve legal issue\n\n"
            "I write regarding the following issue:\n"
            f"{issue}\n\n"
            "I request that this matter be addressed in writing within [number] days so that we may keep a clear record.\n\n"
            "Documents I can provide include: [receipts/messages/agreement/other proof].\n\n"
            "Yours faithfully,\n[Your name]"
        )
    return json.dumps({
        "mode": "document_draft",
        "title": draft_title,
        "document_type": document_type,
        "draft_text": body,
        "needs_review": needs_review,
        "review_reason": "This document may need a lawyer/admin review before official use." if needs_review else "Basic draft only; review before sending.",
        "sources": sources,
        "paid_service": {
            "mode": "paid_service_prompt",
            "service_type": "lawyer_review" if needs_review else "document_certification",
            "title": "Send document for review",
            "description": "Demo paid step. Later this can send the draft to a lawyer/admin for review or certification.",
            "amount_usd": "2.00",
            "button_label": "Pay & submit demo",
        },
    })


@tool
def recommend_paid_service(issue: str, service_type: str = "document_certification") -> str:
    """Return a paid-service prompt for demo payment UI."""
    labels = {
        "document_certification": "Document certification request",
        "lawyer_review": "Lawyer document review",
        "appointment_request": "Lawyer appointment request",
    }
    title = labels.get(service_type, "Service request")
    return json.dumps({
        "mode": "paid_service_prompt",
        "service_type": service_type,
        "title": title,
        "description": "This is a demo paid step. The AI does not certify documents itself; it submits the request for a relevant person or authority.",
        "amount_usd": "2.00",
        "button_label": "Pay & submit demo",
    })


@tool
def create_admin_review_request(issue: str, reason: str = "Needs human review", city: str = "", priority: str = "normal") -> str:
    """Create a human/admin review request when the AI lacks verified sources or the matter is risky."""
    area = detect_practice_area(issue)
    priority = priority if priority in ["low", "normal", "high", "urgent"] else "normal"
    obj = AdminReviewRequest.objects.create(
        user_prompt=issue,
        issue_type=area,
        reason=reason,
        city=city or "",
        source_mode="civilian_agent",
        priority=priority,
        metadata={"created_by": "civilian_agent_tool"},
    )
    return json.dumps({
        "mode": "admin_review",
        "review_id": obj.id,
        "title": "Sent for admin review",
        "issue_type": area,
        "priority": priority,
        "message": "This request has been added to the admin review queue.",
        "reason": reason,
    })
