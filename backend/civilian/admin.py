from django.contrib import admin

from .models import (
    AdminNotification,
    CitizenMatter,
    DocumentReviewRequest,
    GeneratedDocument,
    KnowledgeBaseFailure,
    KnowledgeBaseNote,
    Lawyer,
    LawyerAssignment,
    LawyerBadge,
    MatterAttachment,
    MatterPayment,
    PathwayDocumentTemplate,
    PlatformSetting,
)


@admin.register(PathwayDocumentTemplate)
class PathwayDocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "matter_type", "document_type", "active", "version", "requires_practitioner_review", "requires_certification_or_stamp", "updated_at")
    list_filter = ("matter_type", "document_type", "active", "requires_practitioner_review", "requires_certification_or_stamp")
    search_fields = ("title", "support_note", "last_reviewed_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(KnowledgeBaseNote)
class KnowledgeBaseNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "matter_type", "topic", "verified", "visible_to_citizen", "active", "updated_at")
    list_filter = ("matter_type", "topic", "verified", "visible_to_citizen", "active")
    search_fields = ("title", "body", "tags")


class MatterAttachmentInline(admin.TabularInline):
    model = MatterAttachment
    extra = 0
    fields = ("category", "payment", "title", "file", "note", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class MatterPaymentInline(admin.TabularInline):
    model = MatterPayment
    extra = 0


@admin.register(CitizenMatter)
class CitizenMatterAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "matter_type", "status", "updated_at")
    list_filter = ("matter_type", "status")
    search_fields = ("title", "intake_json", "generated_document_text")
    readonly_fields = ("created_at", "updated_at")
    inlines = [MatterPaymentInline, MatterAttachmentInline]


@admin.register(MatterAttachment)
class MatterAttachmentAdmin(admin.ModelAdmin):
    list_display = ("title", "matter", "payment", "category", "uploaded_at")
    list_filter = ("category",)
    search_fields = ("title", "note", "matter__title")


@admin.register(MatterPayment)
class MatterPaymentAdmin(admin.ModelAdmin):
    list_display = ("matter", "due_date", "amount", "currency", "status", "paid_date", "amount_paid")
    list_filter = ("status", "currency")


@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "city", "verified", "available_for_appointments", "is_active")
    list_filter = ("verified", "available_for_appointments", "is_active", "city")
    search_fields = ("full_name", "firm_name", "email", "phone")
    filter_horizontal = ("badges",)


@admin.register(LawyerBadge)
class LawyerBadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "assigned_by_admin_only")


@admin.register(DocumentReviewRequest)
class DocumentReviewRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "assigned_lawyer", "review_type", "status", "updated_at")
    list_filter = ("status", "review_type")
    search_fields = ("user__email", "user_note", "admin_note", "lawyer_note")


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "user", "status", "created_at")
    list_filter = ("document_type", "status")


@admin.register(LawyerAssignment)
class LawyerAssignmentAdmin(admin.ModelAdmin):
    list_display = ("lawyer", "matter", "document_review", "status", "created_at")


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "priority", "is_read", "created_at")
    list_filter = ("type", "priority", "is_read")


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "is_public", "updated_at")


@admin.register(KnowledgeBaseFailure)
class KnowledgeBaseFailureAdmin(admin.ModelAdmin):
    list_display = ("user", "source_count", "resolved", "created_at")
    list_filter = ("resolved",)
