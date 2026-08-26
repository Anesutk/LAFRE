from __future__ import annotations

from rest_framework import serializers

from .models import (
    CitizenMatter,
    DocumentReviewRequest,
    KnowledgeBaseNote,
    Lawyer,
    LawyerBadge,
    MatterAttachment,
    MatterPayment,
    PathwayDocumentTemplate,
)


def clean_file_label(file_field):
    if not file_field:
        return ""
    return file_field.name.split("/")[-1]


class PathwayDocumentTemplateSerializer(serializers.ModelSerializer):
    matter_type_display = serializers.CharField(source="get_matter_type_display", read_only=True)
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    template_file_label = serializers.SerializerMethodField()

    class Meta:
        model = PathwayDocumentTemplate
        fields = [
            "id", "matter_type", "matter_type_display", "document_type", "document_type_display",
            "title", "description", "template_file", "template_file_label", "support_note",
            "requires_practitioner_review", "requires_certification_or_stamp", "active", "sort_order",
            "version", "last_reviewed_by", "review_date", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "template_file_label", "created_at", "updated_at"]

    def get_template_file_label(self, obj):
        return clean_file_label(obj.template_file)


class KnowledgeBaseNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBaseNote
        fields = ["id", "title", "body", "tags", "matter_type", "topic", "verified", "visible_to_citizen", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class MatterAttachmentSerializer(serializers.ModelSerializer):
    file_label = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    clean_view_url = serializers.SerializerMethodField()
    clean_download_url = serializers.SerializerMethodField()

    class Meta:
        model = MatterAttachment
        fields = [
            "id", "matter", "payment", "category", "category_display", "title", "file", "file_label",
            "clean_view_url", "clean_download_url", "note", "metadata", "uploaded_at",
        ]
        read_only_fields = ["id", "matter", "file_label", "clean_view_url", "clean_download_url", "uploaded_at", "category_display"]

    def get_file_label(self, obj):
        return clean_file_label(obj.file)

    def get_clean_view_url(self, obj):
        return f"/api/civilian/documents/attachments/{obj.id}/view/"

    def get_clean_download_url(self, obj):
        return f"/api/civilian/documents/attachments/{obj.id}/download/"


class MatterPaymentSerializer(serializers.ModelSerializer):
    receipts = MatterAttachmentSerializer(many=True, read_only=True)
    receipt_count = serializers.SerializerMethodField()

    class Meta:
        model = MatterPayment
        fields = [
            "id", "due_date", "amount", "currency", "status", "paid_date", "amount_paid", "notes",
            "receipt_count", "receipts", "created_at",
        ]
        read_only_fields = ["id", "receipt_count", "receipts", "created_at"]

    def get_receipt_count(self, obj):
        try:
            return obj.receipts.count()
        except Exception:
            return 0


class CitizenMatterSerializer(serializers.ModelSerializer):
    attachments = MatterAttachmentSerializer(many=True, read_only=True)
    payments = MatterPaymentSerializer(many=True, read_only=True)
    document_template_title = serializers.CharField(source="document_template.title", read_only=True)
    generated_document_view_url = serializers.SerializerMethodField()
    generated_document_download_url = serializers.SerializerMethodField()
    upload_counts = serializers.SerializerMethodField()

    class Meta:
        model = CitizenMatter
        fields = [
            "id", "matter_type", "title", "status", "intake_json", "validation_json", "kb_support_json",
            "smart_summary_json", "document_template", "document_template_title", "generated_document_text",
            "generated_document_view_url", "generated_document_download_url", "attachments", "payments",
            "upload_counts", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_generated_document_view_url(self, obj):
        return f"/api/civilian/citizen/matters/{obj.id}/document/view/"

    def get_generated_document_download_url(self, obj):
        return f"/api/civilian/citizen/matters/{obj.id}/document/download/"

    def get_upload_counts(self, obj):
        counts = {}
        for row in obj.attachments.values("category").order_by("category"):
            counts[row["category"]] = counts.get(row["category"], 0) + 1
        return counts


class LawyerBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerBadge
        fields = ["id", "name", "description", "assigned_by_admin_only"]


class LawyerSerializer(serializers.ModelSerializer):
    badges = LawyerBadgeSerializer(many=True, read_only=True)

    class Meta:
        model = Lawyer
        fields = [
            "id", "full_name", "firm_name", "slug", "practice_areas", "services", "languages", "badges",
            "city", "province", "address", "email", "phone", "website", "years_experience",
            "consultation_mode", "consultation_fee_usd", "accepts_free_legal_aid", "available_for_appointments",
            "verified", "verification_note", "verification_documents", "bio", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DocumentReviewRequestSerializer(serializers.ModelSerializer):
    assigned_lawyer_name = serializers.CharField(source="assigned_lawyer.full_name", read_only=True)

    class Meta:
        model = DocumentReviewRequest
        fields = [
            "id", "user", "document", "assigned_lawyer", "assigned_lawyer_name", "review_type", "status",
            "user_note", "admin_note", "lawyer_note", "reviewed_file", "signed_or_stamped_file", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]
