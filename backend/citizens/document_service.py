from io import BytesIO
from pathlib import Path
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from textwrap import wrap


def value(answers, key, default='__________'):
    v = answers.get(key)
    if v is None or v == '' or v is False:
        return default
    if v is True:
        return 'Yes'
    return str(v)


def money(answers, amount_key='amount'):
    cur = value(answers, 'currency', 'USD')
    amt = value(answers, amount_key, '__________')
    return f'{cur} {amt}'


def generate_title(pathway_key, answers):
    if pathway_key == 'loan-agreement':
        borrower = value(answers, 'borrower_name', 'Borrower')
        amount = money(answers)
        return f'Loan to {borrower} — {amount}'
    if pathway_key == 'contract-of-sale':
        desc = value(answers, 'property_description', 'Property')
        short = desc[:45] + ('...' if len(desc) > 45 else '')
        return f'Sale of {short}'
    if pathway_key == 'affidavit-of-debt':
        other = value(answers, 'other_party_name', 'Other Party')
        return f'Affidavit of Debt — {other}'
    return 'Citizen Matter'


def assess_flags(pathway_key, answers):
    flags = []
    if pathway_key == 'loan-agreement':
        try:
            rate = float(answers.get('interest_rate') or 0)
        except Exception:
            rate = 0
        if answers.get('interest_type') == 'Monthly interest' and rate > 0:
            flags.append('Interest was added. Consider lawyer review before signing.')
        if rate > 5:
            flags.append('High monthly interest detected. This should be reviewed by a registered legal practitioner.')
        if answers.get('late_penalty'):
            flags.append('Late penalty added. Keep penalties fair and review if unsure.')
        if answers.get('has_collateral') == 'Yes':
            flags.append('Collateral added. Do not enforce collateral by force; seek legal help if there is a dispute.')
    if pathway_key == 'contract-of-sale':
        flags.append('Property sale is high risk. Lawyer/conveyancer review is strongly recommended.')
    if pathway_key == 'affidavit-of-debt':
        flags.append('This draft is not sworn until signed before a Commissioner of Oaths.')
    return flags


def next_steps(pathway_key):
    if pathway_key == 'loan-agreement':
        return [
            'Read the draft carefully and correct any wrong information.',
            'Download or print the PDF.',
            'Both lender and borrower should sign, preferably with witnesses.',
            'Upload proof of payment, IDs, and the signed copy to the evidence locker.',
            'Send for lawyer review if interest, penalties, collateral, or large sums are involved.',
        ]
    if pathway_key == 'contract-of-sale':
        return [
            'Do not sign or pay large sums before title and ownership checks.',
            'Download or print the draft for review.',
            'Send the draft to a lawyer/conveyancer before signing.',
            'Upload title deed, IDs, rates clearance, and payment proof where available.',
            'Keep all transfer, ZIMRA, and conveyancing records in the matter file.',
        ]
    if pathway_key == 'affidavit-of-debt':
        return [
            'Read the affidavit and ensure every fact is true.',
            'Print the draft and take your ID to a Commissioner of Oaths.',
            'Sign only in front of the Commissioner of Oaths.',
            'Upload the sworn/stamped copy to your evidence locker.',
            'Seek lawyer review if court action or disputed facts are involved.',
        ]
    return ['Review, download, print, and save your matter records.']


def summary_for(pathway_key, answers):
    if pathway_key == 'loan-agreement':
        return (
            f"{value(answers, 'lender_name', 'The lender')} is lending {money(answers)} to "
            f"{value(answers, 'borrower_name', 'the borrower')}. The money is for "
            f"{value(answers, 'loan_purpose', 'the stated purpose')}. Repayment is due by "
            f"{value(answers, 'due_date', 'the agreed due date')} by {value(answers, 'payment_method', 'the agreed payment method')}. "
            f"Interest: {value(answers, 'interest_type', 'Interest-free')}."
        )
    if pathway_key == 'contract-of-sale':
        return (
            f"{value(answers, 'seller_name', 'The seller')} is selling property described as "
            f"{value(answers, 'property_description', 'the property')} to {value(answers, 'purchaser_name', 'the purchaser')} "
            f"for {money(answers, 'purchase_price')}. Occupation is planned for {value(answers, 'occupation_date', 'the agreed date')}. "
            "Because this involves property transfer, professional review is strongly recommended."
        )
    if pathway_key == 'affidavit-of-debt':
        return (
            f"{value(answers, 'deponent_name', 'The deponent')} states that {value(answers, 'other_party_name', 'the other party')} "
            f"owes {money(answers)} from a loan/debt dated {value(answers, 'loan_date', 'the stated date')}, due by "
            f"{value(answers, 'due_date', 'the due date')}. This draft must be sworn before a Commissioner of Oaths."
        )
    return 'Matter summary unavailable.'


def document_text(pathway_key, answers):
    disclaimer = (
        "\n\nDISCLAIMER: This document is generated by LAFRE Citizens as legal information and document preparation support. "
        "It is not legal advice. Only a registered legal practitioner can provide legal advice, review, certify, validate, or represent you.\n"
    )
    if pathway_key == 'loan-agreement':
        return f"""
LOAN AGREEMENT
Made with guided legal information support

DATE OF AGREEMENT: {value(answers, 'money_given_date')}

1. THE PARTIES
1.1 LENDER
Full Name: {value(answers, 'lender_name')}
I.D No: {value(answers, 'lender_id')}
Phone: {value(answers, 'lender_phone')}
Physical Address: {value(answers, 'lender_address')}
Nationality: {value(answers, 'lender_nationality')}

1.2 BORROWER
Full Name: {value(answers, 'borrower_name')}
I.D No: {value(answers, 'borrower_id')}
Phone: {value(answers, 'borrower_phone')}
Physical Address: {value(answers, 'borrower_address')}
Nationality: {value(answers, 'borrower_nationality')}

2. LOAN DETAILS
The Lender lends to the Borrower, and the Borrower acknowledges receipt of, the principal sum of {money(answers)}.
Amount in words: {value(answers, 'amount_words')}
Purpose of the loan: {value(answers, 'loan_purpose')}
Date money is/will be given: {value(answers, 'money_given_date')}
Proof of payment: {value(answers, 'proof_available')}

3. REPAYMENT
Repayment type: {value(answers, 'repayment_type')}
Final due date: {value(answers, 'due_date')}
Payment method: {value(answers, 'payment_method')}
Payment details: {value(answers, 'payment_details')}
Early repayment is allowed without penalty unless both parties agree otherwise in writing.

4. INTEREST AND PENALTY
Interest: {value(answers, 'interest_type', 'Interest-free')}
Interest rate per month: {value(answers, 'interest_rate', '0')}%
Late payment penalty: {value(answers, 'late_penalty', 'None stated')}
Legal collection costs: {value(answers, 'legal_costs')}

5. SECURITY / COLLATERAL
Collateral provided: {value(answers, 'has_collateral')}
Collateral description: {value(answers, 'collateral_description')}
Estimated collateral value: {value(answers, 'collateral_value')}
The parties understand that collateral terms should be enforced only through lawful processes.

6. GOVERNING LAW
This Agreement shall be governed by the laws of Zimbabwe.

7. GENERAL
This is the entire agreement between the parties. Any changes must be in writing and signed by both parties.

SIGNED AT {value(answers, 'signing_city')} ON ______________________

LENDER SIGNATURE: ______________________
BORROWER SIGNATURE: ____________________

WITNESSES
1. {value(answers, 'witness_1')} Signature: ____________________
2. {value(answers, 'witness_2')} Signature: ____________________
""" + disclaimer
    if pathway_key == 'contract-of-sale':
        return f"""
MEMORANDUM OF AGREEMENT OF SALE

SELLER DETAILS
I.D No: {value(answers, 'seller_id')}
Name: {value(answers, 'seller_name')}
Physical Address: {value(answers, 'seller_address')}
Nationality: {value(answers, 'seller_nationality')}

PURCHASER DETAILS
I.D No: {value(answers, 'purchaser_id')}
Name: {value(answers, 'purchaser_name')}
Physical Address: {value(answers, 'purchaser_address')}
Nationality: {value(answers, 'purchaser_nationality')}

The seller and purchaser are referred to as the parties.

1. THE PROPERTY
The seller sells to the purchaser a certain piece of land/property situated in the district of {value(answers, 'district')} being:
Description: {value(answers, 'property_description')}
Measuring: {value(answers, 'measurement')}
Held under Deed of Transfer: {value(answers, 'deed_number')}

2. PRICE
The purchase price is {money(answers, 'purchase_price')}.
Deposit: {value(answers, 'deposit', 'No deposit stated')}
Balance payment terms: {value(answers, 'balance_terms')}

3. CONVEYANCING AND TRANSFER
Conveyancer/Law Firm: {value(answers, 'conveyancer')}
Transfer costs shall be borne by: {value(answers, 'transfer_costs_by')}
Capital Gains Tax clearance responsibility: {value(answers, 'cgt_by')}

4. POSSESSION AND OCCUPATION
Vacant possession/occupation shall be given on: {value(answers, 'occupation_date')}

5. VOET-STOOTS / AS IS
The property is sold as it stands at the date of this agreement, subject to lawful disclosures and professional review.

6. BREACH
If either party fails to comply and remains in default after written notice to remedy, the aggrieved party may seek lawful remedies.

7. DOMICILIUM
The parties choose their addresses above for service of notices and legal process.

SIGNED AT ____________________ ON ____________________
BUYER SIGNATURE: ______________________
SELLER SIGNATURE: _____________________
WITNESS 1: ____________________________
WITNESS 2: ____________________________
""" + disclaimer + "\nIMPORTANT: Property sale documents should be reviewed by a lawyer/conveyancer before signing or transfer.\n"
    if pathway_key == 'affidavit-of-debt':
        return f"""
AFFIDAVIT OF DEBT

IN THE MAGISTRATES COURT FOR THE PROVINCE OF: {value(answers, 'province')}
HELD AT: {value(answers, 'held_at')}
CASE NO: {value(answers, 'case_number')}

IN THE MATTER BETWEEN:
{value(answers, 'deponent_name')} APPLICANT / LENDER
AND
{value(answers, 'other_party_name')} RESPONDENT / BORROWER

I, {value(answers, 'deponent_name')}, ID No. {value(answers, 'deponent_id')}, of {value(answers, 'deponent_address')}, do hereby make oath and state as follows:

1. The facts stated in this affidavit are within my personal knowledge and are true and correct to the best of my knowledge.
2. On {value(answers, 'loan_date')}, I entered into a loan/debt arrangement with {value(answers, 'other_party_name')}, ID No. {value(answers, 'other_party_id')}, of {value(answers, 'other_party_address')}.
3. The amount owed is {money(answers)}.
4. Purpose of the loan/debt: {value(answers, 'purpose')}.
5. The amount was due by {value(answers, 'due_date')}.
6. Proof available: {value(answers, 'proof_description')}.
7. Interest terms: {value(answers, 'interest_terms', 'None stated')}.
8. Collateral/security: {value(answers, 'collateral_terms', 'None stated')}.
9. I understand that making false statements in a sworn affidavit may have legal consequences.

SIGNED AND SWORN TO BY:
DEPONENT: ______________________ DATE: ______________________

COMMISSIONER OF OATHS
Full Name: {value(answers, 'commissioner_name')}
Designation: {value(answers, 'commissioner_designation')}
Official Stamp: ______________________
Place of signing: {value(answers, 'signing_place')}
""" + disclaimer + "\nIMPORTANT: This draft only becomes a sworn affidavit when signed before a Commissioner of Oaths.\n"
    return disclaimer


def create_pdf_file(generated_document):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 22 * mm
    top = height - 22 * mm
    y = top

    c.setTitle(generated_document.matter.title)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(left, y, 'LAFRE Citizens')
    y -= 6 * mm
    c.setFont('Helvetica', 8)
    c.drawString(left, y, 'Legal information, not legal advice. Only registered legal practitioners can give legal advice.')
    y -= 9 * mm
    c.line(left, y, width - left, y)
    y -= 8 * mm

    c.setFont('Helvetica-Bold', 12)
    c.drawString(left, y, generated_document.matter.title[:90])
    y -= 9 * mm
    c.setFont('Helvetica', 9.5)

    for raw_line in generated_document.content.splitlines():
        line = raw_line.rstrip()
        if not line:
            y -= 4 * mm
            continue
        if line.isupper() and len(line) < 70:
            c.setFont('Helvetica-Bold', 10.5)
            wrapped = wrap(line, 92) or ['']
        else:
            c.setFont('Helvetica', 9.2)
            wrapped = wrap(line, 98) or ['']
        for part in wrapped:
            if y < 22 * mm:
                c.showPage()
                y = top
                c.setFont('Helvetica', 9.2)
            c.drawString(left, y, part)
            y -= 5 * mm
    c.save()
    buffer.seek(0)
    filename = f'matter_{generated_document.matter_id}_v{generated_document.version}.pdf'
    generated_document.pdf_file.save(filename, ContentFile(buffer.read()), save=True)
    return generated_document.pdf_file
