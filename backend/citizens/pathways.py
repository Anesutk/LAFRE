PATHWAYS = {
    "loan-agreement": {
        "key": "loan-agreement",
        "title": "Loan Agreement",
        "short_title": "Loan",
        "description": "Create a written repayment agreement between lender and borrower.",
        "risk_level": "Medium",
        "estimated_time": "15–20 min",
        "fixed_review_fee": "3.00",
        "documents_needed": ["Lender ID", "Borrower ID", "Proof of payment", "Collateral proof if any"],
        "legal_notice": "This is legal information and document preparation support, not legal advice. High interest, unfair penalties, or unclear collateral terms should be reviewed by a registered legal practitioner.",
        "steps": [
            {"key": "lender", "title": "Lender Details", "help": "Tell us about the person lending the money.", "questions": [
                {"key": "lender_name", "label": "Full name of lender", "type": "text", "required": True, "placeholder": "e.g. Trust Fastino Maera"},
                {"key": "lender_id", "label": "Lender ID number", "type": "text", "required": True, "placeholder": "e.g. 07-203934X07"},
                {"key": "lender_phone", "label": "Lender phone number", "type": "text", "required": True, "placeholder": "e.g. 078 066 9218"},
                {"key": "lender_address", "label": "Lender physical address", "type": "textarea", "required": True, "placeholder": "House number, street, suburb, city"},
                {"key": "lender_nationality", "label": "Lender nationality", "type": "text", "required": True, "placeholder": "e.g. Zimbabwean"},
            ]},
            {"key": "borrower", "title": "Borrower Details", "help": "Tell us about the person borrowing the money.", "questions": [
                {"key": "borrower_name", "label": "Full name of borrower", "type": "text", "required": True, "placeholder": "e.g. Tanaka Moyo"},
                {"key": "borrower_id", "label": "Borrower ID number", "type": "text", "required": True, "placeholder": "e.g. 63-123456A63"},
                {"key": "borrower_phone", "label": "Borrower phone number", "type": "text", "required": True, "placeholder": "e.g. 077 000 0000"},
                {"key": "borrower_address", "label": "Borrower physical address", "type": "textarea", "required": True, "placeholder": "House number, street, suburb, city"},
                {"key": "borrower_nationality", "label": "Borrower nationality", "type": "text", "required": True, "placeholder": "e.g. Zimbabwean"},
            ]},
            {"key": "loan", "title": "Loan Details", "help": "Describe the money being lent and why.", "questions": [
                {"key": "currency", "label": "Currency", "type": "select", "required": True, "options": ["USD", "ZiG"]},
                {"key": "amount", "label": "Loan amount", "type": "number", "required": True, "placeholder": "2650"},
                {"key": "amount_words", "label": "Amount in words", "type": "text", "required": False, "placeholder": "Two thousand six hundred and fifty United States Dollars"},
                {"key": "loan_purpose", "label": "Purpose of the loan", "type": "textarea", "required": True, "placeholder": "e.g. business capital, emergency, school fees"},
                {"key": "money_given_date", "label": "Date money is/will be given", "type": "date", "required": True},
                {"key": "proof_available", "label": "Do you have proof of payment?", "type": "select", "required": True, "options": ["Yes", "No", "Will upload later"]},
            ]},
            {"key": "repayment", "title": "Repayment Terms", "help": "Set how and when the borrower must pay back.", "questions": [
                {"key": "repayment_type", "label": "Repayment type", "type": "select", "required": True, "options": ["Single payment", "Installments"]},
                {"key": "due_date", "label": "Final due date", "type": "date", "required": True},
                {"key": "payment_method", "label": "Payment method", "type": "select", "required": True, "options": ["Cash", "Bank transfer", "EcoCash", "Other"]},
                {"key": "payment_details", "label": "Payment details", "type": "textarea", "required": False, "placeholder": "Bank/account/mobile number if you want it in the agreement"},
            ]},
            {"key": "interest", "title": "Interest & Penalty", "help": "Interest and penalties can create legal risk. Keep them fair and consider lawyer review.", "questions": [
                {"key": "interest_type", "label": "Interest", "type": "select", "required": True, "options": ["Interest-free", "Monthly interest"]},
                {"key": "interest_rate", "label": "Interest rate per month (%)", "type": "number", "required": False, "placeholder": "0"},
                {"key": "late_penalty", "label": "Late payment penalty", "type": "text", "required": False, "placeholder": "e.g. USD 5 per week"},
                {"key": "legal_costs", "label": "Should borrower cover lawful collection costs if default happens?", "type": "select", "required": True, "options": ["Yes", "No", "Lawyer review needed"]},
            ]},
            {"key": "security", "title": "Security / Collateral", "help": "Collateral should be clearly described. Do not take it by force if there is a dispute.", "questions": [
                {"key": "has_collateral", "label": "Is there collateral/security?", "type": "select", "required": True, "options": ["No", "Yes"]},
                {"key": "collateral_description", "label": "Collateral description", "type": "textarea", "required": False, "placeholder": "e.g. HP laptop, serial number, condition"},
                {"key": "collateral_value", "label": "Estimated collateral value", "type": "text", "required": False, "placeholder": "e.g. USD 400"},
            ]},
            {"key": "witnesses", "title": "Witnesses", "help": "Witnesses help prove that the parties signed willingly.", "questions": [
                {"key": "witness_1", "label": "Witness 1 name and ID", "type": "text", "required": False},
                {"key": "witness_2", "label": "Witness 2 name and ID", "type": "text", "required": False},
                {"key": "signing_city", "label": "City/town of signing", "type": "text", "required": True, "placeholder": "e.g. Harare"},
            ]},
            {"key": "review", "title": "Review & Confirm", "help": "Confirm that the information is true and complete.", "questions": [
                {"key": "truth_confirmed", "label": "I confirm the details are true and complete", "type": "checkbox", "required": True},
                {"key": "lawyer_review_preference", "label": "Would you like lawyer review after generating?", "type": "select", "required": True, "options": ["Not now", "Yes, show me review option"]},
            ]},
        ],
    },
    "contract-of-sale": {
        "key": "contract-of-sale",
        "title": "Contract of Sale",
        "short_title": "Sale",
        "description": "Prepare an agreement for sale of property or land.",
        "risk_level": "High",
        "estimated_time": "20–30 min",
        "fixed_review_fee": "10.00",
        "documents_needed": ["Seller ID", "Purchaser ID", "Title deed", "Rates clearance", "ZIMRA/CGT information"],
        "legal_notice": "Property sale documents should be checked by a lawyer or conveyancer before signing or transfer.",
        "steps": [
            {"key": "seller", "title": "Seller Details", "help": "Tell us about the seller.", "questions": [
                {"key": "seller_name", "label": "Seller full name", "type": "text", "required": True},
                {"key": "seller_id", "label": "Seller ID number", "type": "text", "required": True},
                {"key": "seller_address", "label": "Seller physical address", "type": "textarea", "required": True},
                {"key": "seller_nationality", "label": "Seller nationality", "type": "text", "required": True},
            ]},
            {"key": "purchaser", "title": "Purchaser Details", "help": "Tell us about the purchaser.", "questions": [
                {"key": "purchaser_name", "label": "Purchaser full name", "type": "text", "required": True},
                {"key": "purchaser_id", "label": "Purchaser ID number", "type": "text", "required": True},
                {"key": "purchaser_address", "label": "Purchaser physical address", "type": "textarea", "required": True},
                {"key": "purchaser_nationality", "label": "Purchaser nationality", "type": "text", "required": True},
            ]},
            {"key": "property", "title": "Property Details", "help": "Use details from the title deed where possible.", "questions": [
                {"key": "district", "label": "District", "type": "text", "required": True},
                {"key": "property_description", "label": "Property description", "type": "textarea", "required": True, "placeholder": "Stand number, township, legal description"},
                {"key": "measurement", "label": "Measurement/size", "type": "text", "required": True},
                {"key": "deed_number", "label": "Deed of transfer number/year", "type": "text", "required": True},
            ]},
            {"key": "price", "title": "Price & Payment", "help": "Set the purchase price and payment terms.", "questions": [
                {"key": "currency", "label": "Currency", "type": "select", "required": True, "options": ["USD", "ZiG"]},
                {"key": "purchase_price", "label": "Purchase price", "type": "number", "required": True},
                {"key": "deposit", "label": "Deposit amount", "type": "number", "required": False},
                {"key": "balance_terms", "label": "Balance payment terms", "type": "textarea", "required": True},
            ]},
            {"key": "transfer", "title": "Transfer & Costs", "help": "Property transfer usually requires conveyancing and professional checks.", "questions": [
                {"key": "conveyancer", "label": "Conveyancer/law firm if known", "type": "text", "required": False},
                {"key": "transfer_costs_by", "label": "Who pays transfer costs?", "type": "select", "required": True, "options": ["Purchaser", "Seller", "To be agreed by lawyer"]},
                {"key": "cgt_by", "label": "Who handles Capital Gains Tax clearance?", "type": "select", "required": True, "options": ["Seller", "To be agreed by lawyer"]},
                {"key": "occupation_date", "label": "Vacant possession/occupation date", "type": "date", "required": True},
            ]},
            {"key": "confirm", "title": "Review & Confirm", "help": "Confirm this draft needs lawyer/conveyancer review before signing.", "questions": [
                {"key": "truth_confirmed", "label": "I confirm the details are true and complete", "type": "checkbox", "required": True},
                {"key": "review_understood", "label": "I understand property sale documents should be reviewed", "type": "checkbox", "required": True},
            ]},
        ],
    },
    "affidavit-of-debt": {
        "key": "affidavit-of-debt",
        "title": "Affidavit of Debt",
        "short_title": "Affidavit",
        "description": "Prepare a formal sworn statement about a debt.",
        "risk_level": "Medium",
        "estimated_time": "15–25 min",
        "fixed_review_fee": "5.00",
        "documents_needed": ["ID", "Loan agreement", "Proof of debt/payment", "Borrower details"],
        "legal_notice": "A draft affidavit only becomes sworn when signed before a Commissioner of Oaths. False sworn statements can have legal consequences.",
        "steps": [
            {"key": "court", "title": "Court & Matter", "help": "These can be left blank if you do not yet have a case number.", "questions": [
                {"key": "province", "label": "Province", "type": "text", "required": False},
                {"key": "held_at", "label": "Held at", "type": "text", "required": False},
                {"key": "case_number", "label": "Case number", "type": "text", "required": False},
            ]},
            {"key": "parties", "title": "Parties", "help": "Enter the person swearing the affidavit and the other party.", "questions": [
                {"key": "deponent_name", "label": "Your full name", "type": "text", "required": True},
                {"key": "deponent_id", "label": "Your ID number", "type": "text", "required": True},
                {"key": "deponent_address", "label": "Your physical address", "type": "textarea", "required": True},
                {"key": "other_party_name", "label": "Other party full name", "type": "text", "required": True},
                {"key": "other_party_id", "label": "Other party ID if known", "type": "text", "required": False},
                {"key": "other_party_address", "label": "Other party address if known", "type": "textarea", "required": False},
            ]},
            {"key": "debt", "title": "Debt Details", "help": "State what happened in simple factual terms.", "questions": [
                {"key": "loan_date", "label": "Date of loan/agreement", "type": "date", "required": True},
                {"key": "currency", "label": "Currency", "type": "select", "required": True, "options": ["USD", "ZiG"]},
                {"key": "amount", "label": "Amount owed", "type": "number", "required": True},
                {"key": "purpose", "label": "Purpose of the loan/debt", "type": "textarea", "required": True},
                {"key": "due_date", "label": "Due date", "type": "date", "required": True},
            ]},
            {"key": "proof", "title": "Proof & Declarations", "help": "Tell us what proof exists and confirm the facts are true.", "questions": [
                {"key": "proof_description", "label": "Proof available", "type": "textarea", "required": False, "placeholder": "Payment receipt, WhatsApp messages, signed loan agreement"},
                {"key": "interest_terms", "label": "Interest terms if any", "type": "text", "required": False},
                {"key": "collateral_terms", "label": "Collateral/security if any", "type": "textarea", "required": False},
                {"key": "truth_confirmed", "label": "I confirm that the facts are true to the best of my knowledge", "type": "checkbox", "required": True},
            ]},
            {"key": "commissioner", "title": "Commissioner of Oaths", "help": "This section can be completed when you swear the affidavit.", "questions": [
                {"key": "commissioner_name", "label": "Commissioner name if known", "type": "text", "required": False},
                {"key": "commissioner_designation", "label": "Commissioner designation if known", "type": "text", "required": False},
                {"key": "signing_place", "label": "Place of signing", "type": "text", "required": False},
            ]},
        ],
    },
}


def list_pathways():
    return [{k: v for k, v in p.items() if k != 'steps'} for p in PATHWAYS.values()]


def get_pathway(key: str):
    return PATHWAYS.get(key)


def all_question_keys(pathway):
    keys = []
    for step in pathway.get('steps', []):
        for q in step.get('questions', []):
            keys.append(q['key'])
    return keys
