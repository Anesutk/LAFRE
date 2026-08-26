from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.http import FileResponse, HttpResponse
from django.db import OperationalError
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.auth import get_user_from_request, is_admin_user
from accounts.models import UserProfile
from .lending_pathway import default_document, fill_placeholders, context as loan_context, extract_template_text
from .models import (
    AdminNotification,
    CitizenMatter,
    DocumentReviewRequest,
    GeneratedDocument,
    KnowledgeBaseNote,
    Lawyer,
    MatterAttachment,
    MatterPayment,
    PathwayDocumentTemplate,
)
from .serializers import (
    CitizenMatterSerializer,
    DocumentReviewRequestSerializer,
    KnowledgeBaseNoteSerializer,
    LawyerSerializer,
    MatterAttachmentSerializer,
    PathwayDocumentTemplateSerializer,
)


def require_citizen(request):
    user = get_user_from_request(request)
    if not user:
        return None, None, Response({"ok": False, "detail": "Sign in to LAFRE Citizen first."}, status=401)
    profile = getattr(user, "lafre_profile", None)
    if not profile or not profile.can_use_civilian:
        return user, profile, Response({"ok": False, "detail": "This account does not have LAFRE Citizen access."}, status=403)
    if not profile.is_active_for_platform():
        return user, profile, Response({"ok": False, "detail": "Your LAFRE Citizen account is waiting for admin approval.", "redirect_to": "/citizen/pending"}, status=403)
    return user, profile, None


def require_admin(request):
    user = get_user_from_request(request)
    if not is_admin_user(user):
        return None, Response({"ok": False, "detail": "Admin access required."}, status=403)
    return user, None


def notify_admin(title, message, *, related_user=None, metadata=None, type="citizen_matter", priority="medium"):
    try:
        AdminNotification.objects.create(title=title, message=message, related_user=related_user, metadata=metadata or {}, type=type, priority=priority)
    except Exception:
        pass


def safe_filename(name: str) -> str:
    clean = (name or "document.txt").split("/")[-1]
    for bad in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "s3://"]:
        clean = clean.replace(bad, "redacted")
    return clean


def parse_decimal(value, default="0") -> Decimal:
    try:
        return Decimal(str(value or default).replace(",", ""))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def add_months(start: date, months: int) -> date:
    month = start.month - 1 + months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def find_template():
    return PathwayDocumentTemplate.objects.filter(
        matter_type="lending_money",
        document_type="loan_agreement",
        active=True,
    ).order_by("-version", "sort_order", "-updated_at").first()


def verified_kb_for_lending(form: dict) -> dict:
    notes = list(KnowledgeBaseNote.objects.filter(active=True, verified=True, visible_to_citizen=True).filter(matter_type__in=["", "lending_money"]).order_by("topic", "title")[:8])
    if not notes:
        return {
            "source": "hardcoded_pathway_fallback",
            "verified_guidance_found": False,
            "summary": "No additional verified knowledge-base guidance was found for this matter. LAFRE is showing safe pathway guidance only.",
            "items": [
                "Review the generated agreement carefully before signing.",
                "Both parties should sign and keep copies.",
                "Upload the signed copy and proof that money was given.",
                "Request lawyer review if the amount is high, collateral is involved, terms are unusual, or you need stamping/certification/commissioning guidance.",
            ],
        }
    return {
        "source": "verified_knowledge_base_notes",
        "verified_guidance_found": True,
        "summary": "Verified guidance matched this lending pathway.",
        "items": [{"title": note.title, "topic": note.topic, "body": note.body, "tags": note.tags} for note in notes],
    }


def build_payments(form: dict):
    loan = form.get("loan", {}) or {}
    repayment = form.get("repayment", {}) or {}
    currency = loan.get("currency") or form.get("currency") or "USD"
    total = parse_decimal(loan.get("amount") or form.get("amount"), "0")
    plan = repayment.get("type") or repayment.get("plan") or "single"
    payments = []
    if plan == "instalments" or repayment.get("number_of_instalments"):
        count = int(repayment.get("number_of_instalments") or repayment.get("count") or 1)
        count = max(1, min(count, 120))
        start = parse_date(repayment.get("start_date") or repayment.get("due_date")) or timezone.localdate()
        amount = (total / Decimal(count)).quantize(Decimal("0.01")) if count else total
        for idx in range(count):
            payments.append({"due_date": add_months(start, idx), "amount": amount, "currency": currency, "status": "expected"})
    else:
        due = parse_date(repayment.get("due_date") or loan.get("due_date"))
        payments.append({"due_date": due, "amount": total, "currency": currency, "status": "expected"})
    return payments


def build_smart_summary(form: dict, kb_support: dict) -> dict:
    return {
        "next_steps": [
            "Review the generated loan agreement.",
            "Print or share the agreement with the other party.",
            "Sign with the borrower and witnesses where applicable.",
            "Upload the signed, stamped, certified, or commissioned copy if applicable.",
            "Upload proof that money was given and upload repayment receipts as payments are made.",
            "Request lawyer review if the matter is high value, has collateral, has unusual terms, or you are unsure.",
        ],
        "required_upload_categories": [
            {"category": "signed_document", "label": "Signed / certified / stamped document", "supports_many": True},
            {"category": "proof_of_loan", "label": "Proof money was given", "supports_many": True},
            {"category": "borrower_id", "label": "Borrower ID / identity proof", "supports_many": True},
            {"category": "repayment_evidence", "label": "Repayment receipts", "supports_many": True},
            {"category": "collateral_proof", "label": "Collateral proof", "supports_many": True},
            {"category": "message_evidence", "label": "Messages about the loan", "supports_many": True},
        ],
        "legal_information_notice": "LAFRE provides legal information and document preparation support. It is not a law firm. A legal practitioner should review, stamp, certify, commission, represent, or give legal advice where required.",
        "kb_guidance": kb_support,
    }


def generate_lending_document(form: dict, template: PathwayDocumentTemplate | None):
    if template:
        text = template.extracted_text or extract_template_text(template)
        if text:
            return fill_placeholders(text, loan_context(form))
    return default_document(form)


class CitizenMatterListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, profile, error = require_citizen(request)
        if error:
            return error
        matters = CitizenMatter.objects.filter(user=user).prefetch_related("attachments", "payments__receipts").order_by("-updated_at")
        return Response({"ok": True, "matters": CitizenMatterSerializer(matters, many=True).data})


class LendingCreateMatterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user, profile, error = require_citizen(request)
        if error:
            return error
        form = request.data.get("form") or request.data
        lender_name = (((form.get("lender") or {}).get("full_name")) or form.get("lender_name") or "Lender").strip()
        borrower_name = (((form.get("borrower") or {}).get("full_name")) or form.get("borrower_name") or "Borrower").strip()
        template = find_template()
        kb_support = verified_kb_for_lending(form)
        document_text = generate_lending_document(form, template)
        matter = CitizenMatter.objects.create(
            user=user,
            matter_type="lending_money",
            title=f"Loan Agreement - {lender_name} and {borrower_name}",
            status=CitizenMatter.Status.PENDING_SIGNATURE,
            intake_json=form,
            validation_json={"warnings": []},
            kb_support_json=kb_support,
            smart_summary_json=build_smart_summary(form, kb_support),
            document_template=template,
            generated_document_text=document_text,
        )
        for row in build_payments(form):
            MatterPayment.objects.create(matter=matter, **row)
        notify_admin("New citizen matter", f"{user.get_full_name() or user.email} generated a loan agreement matter.", related_user=user, metadata={"matter_id": matter.id})
        if profile.daily_document_limit:
            profile.consume_document()
        matter = CitizenMatter.objects.prefetch_related("attachments", "payments__receipts").get(id=matter.id)
        return Response({"ok": True, "matter": CitizenMatterSerializer(matter).data}, status=status.HTTP_201_CREATED)


class LendingMatterDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk: int):
        user, profile, error = require_citizen(request)
        if error:
            return error
        matter = CitizenMatter.objects.filter(id=pk, user=user).prefetch_related("attachments", "payments__receipts").first()
        if not matter:
            return Response({"ok": False, "detail": "Matter not found."}, status=404)
        return Response({"ok": True, "matter": CitizenMatterSerializer(matter).data})


class LendingAttachmentUploadView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, pk: int):
        user, profile, error = require_citizen(request)
        if error:
            return error
        matter = CitizenMatter.objects.filter(id=pk, user=user).first()
        if not matter:
            return Response({"ok": False, "detail": "Matter not found."}, status=404)
        if profile.daily_upload_limit and profile.remaining_uploads() <= 0:
            return Response({"ok": False, "detail": "Daily upload limit reached."}, status=429)
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response({"ok": False, "detail": "Choose a file to upload."}, status=400)
        payment = None
        payment_id = request.data.get("payment_id")
        if payment_id:
            payment = MatterPayment.objects.filter(id=payment_id, matter=matter).first()
        attachment = MatterAttachment.objects.create(
            matter=matter,
            payment=payment,
            user=user,
            category=request.data.get("category") or MatterAttachment.Category.OTHER,
            title=request.data.get("title") or safe_filename(uploaded.name),
            file=uploaded,
            note=request.data.get("note") or "",
            metadata={"original_label": safe_filename(uploaded.name)},
        )
        if profile.daily_upload_limit:
            profile.consume_upload()
        return Response({"ok": True, "attachment": MatterAttachmentSerializer(attachment).data}, status=201)


class RequestLawyerReviewView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, pk: int):
        user, profile, error = require_citizen(request)
        if error:
            return error
        matter = CitizenMatter.objects.filter(id=pk, user=user).first()
        if not matter:
            return Response({"ok": False, "detail": "Matter not found."}, status=404)
        generated = GeneratedDocument.objects.create(
            user=user,
            document_type="loan_agreement",
            title=matter.title,
            content=matter.generated_document_text,
            status="draft",
            metadata={"citizen_matter_id": matter.id},
        )
        review = DocumentReviewRequest.objects.create(
            user=user,
            document=generated,
            review_type=request.data.get("review_type") or "review_only",
            status=DocumentReviewRequest.Status.WAITING_ASSIGNMENT,
            user_note=request.data.get("note") or "",
        )
        matter.status = CitizenMatter.Status.REVIEW_REQUESTED
        matter.save(update_fields=["status", "updated_at"])
        notify_admin("Lawyer review requested", f"Review requested for matter {matter.id}.", related_user=user, metadata={"matter_id": matter.id, "review_id": review.id}, priority="high")
        return Response({"ok": True, "review": DocumentReviewRequestSerializer(review).data})


class AttachmentFileView(APIView):
    authentication_classes = []
    permission_classes = []
    as_attachment = False

    def get(self, request, pk: int):
        user = get_user_from_request(request)
        if not user:
            return Response({"ok": False, "detail": "Sign in first."}, status=401)
        qs = MatterAttachment.objects.select_related("matter")
        if not is_admin_user(user):
            qs = qs.filter(matter__user=user)
        attachment = qs.filter(id=pk).first()
        if not attachment or not attachment.file:
            return Response({"ok": False, "detail": "File not found."}, status=404)
        return FileResponse(attachment.file.open("rb"), filename=safe_filename(attachment.title or attachment.file.name), as_attachment=self.as_attachment)


class AttachmentDownloadView(AttachmentFileView):
    as_attachment = True


class MatterDocumentView(APIView):
    authentication_classes = []
    permission_classes = []
    as_attachment = False

    def get(self, request, pk: int):
        user = get_user_from_request(request)
        if not user:
            return Response({"ok": False, "detail": "Sign in first."}, status=401)
        qs = CitizenMatter.objects.all()
        if not is_admin_user(user):
            qs = qs.filter(user=user)
        matter = qs.filter(id=pk).first()
        if not matter:
            return Response({"ok": False, "detail": "Matter not found."}, status=404)
        content = matter.generated_document_text or "No generated document text is available."
        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        filename = safe_filename(f"matter-{matter.id}-loan-agreement.txt")
        disposition = "attachment" if self.as_attachment else "inline"
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        return response


class MatterDocumentDownloadView(MatterDocumentView):
    as_attachment = True


class AdminDocumentTemplateListCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        try:
            templates = PathwayDocumentTemplate.objects.all()
            return Response({"ok": True, "templates": PathwayDocumentTemplateSerializer(templates, many=True).data})
        except OperationalError:
            return Response({"ok": True, "templates": [], "message": "Template tables are not ready. Run migrations to enable this section."})

    def post(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        serializer = PathwayDocumentTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()
        return Response({"ok": True, "template": PathwayDocumentTemplateSerializer(template).data}, status=201)


class AdminDocumentTemplateDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, pk: int):
        admin, error = require_admin(request)
        if error:
            return error
        template = PathwayDocumentTemplate.objects.filter(id=pk).first()
        if not template:
            return Response({"ok": False, "detail": "Template not found."}, status=404)
        serializer = PathwayDocumentTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True, "template": PathwayDocumentTemplateSerializer(template).data})

    def delete(self, request, pk: int):
        admin, error = require_admin(request)
        if error:
            return error
        PathwayDocumentTemplate.objects.filter(id=pk).delete()
        return Response({"ok": True})


class AdminKnowledgeBaseView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        try:
            notes = KnowledgeBaseNote.objects.all().order_by("matter_type", "topic", "title")
            return Response({"ok": True, "notes": KnowledgeBaseNoteSerializer(notes, many=True).data})
        except OperationalError:
            return Response({"ok": True, "notes": [], "message": "Knowledge-base tables are not ready. Run migrations to enable this section."})

    def post(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        serializer = KnowledgeBaseNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save()
        return Response({"ok": True, "note": KnowledgeBaseNoteSerializer(note).data}, status=201)


class AdminCitizenMatterListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        try:
            matters = CitizenMatter.objects.all().prefetch_related("attachments", "payments__receipts")[:300]
            return Response({"ok": True, "matters": CitizenMatterSerializer(matters, many=True).data})
        except OperationalError:
            return Response({"ok": True, "matters": [], "message": "Citizen matter tables are not ready. Run migrations to enable this section."})


class AdminLawyersView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        try:
            return Response({"ok": True, "lawyers": LawyerSerializer(Lawyer.objects.all(), many=True).data})
        except OperationalError:
            return Response({"ok": True, "lawyers": [], "message": "Lawyer tables are not ready. Run migrations to enable this section."})

    def post(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        serializer = LawyerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lawyer = serializer.save()
        return Response({"ok": True, "lawyer": LawyerSerializer(lawyer).data}, status=201)


class AdminReviewQueueView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        try:
            reviews = DocumentReviewRequest.objects.select_related("assigned_lawyer", "user", "document").all()[:300]
            return Response({"ok": True, "reviews": DocumentReviewRequestSerializer(reviews, many=True).data})
        except OperationalError:
            return Response({"ok": True, "reviews": [], "message": "Review tables are not ready. Run migrations to enable this section."})

    def patch(self, request):
        admin, error = require_admin(request)
        if error:
            return error
        review = DocumentReviewRequest.objects.filter(id=request.data.get("review_id")).first()
        if not review:
            return Response({"ok": False, "detail": "Review request not found."}, status=404)
        lawyer_id = request.data.get("assigned_lawyer")
        if lawyer_id:
            review.assigned_lawyer = Lawyer.objects.filter(id=lawyer_id).first()
            review.status = DocumentReviewRequest.Status.ASSIGNED
        if "status" in request.data:
            review.status = request.data["status"]
        if "admin_note" in request.data:
            review.admin_note = request.data["admin_note"]
        review.save()
        return Response({"ok": True, "review": DocumentReviewRequestSerializer(review).data})
