from django.contrib import admin

from .models import ManualAccessToken, PasswordResetToken, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "role", "requested_role", "status", "auth_provider", "city",
        "can_use_civilian", "can_use_student", "can_access_lawyer_portal", "can_access_admin",
        "daily_message_limit", "daily_document_limit", "daily_upload_limit", "created_at",
    )
    list_filter = ("status", "role", "requested_role", "auth_provider", "can_use_civilian", "can_use_student", "can_access_lawyer_portal", "can_access_admin")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "phone", "city", "institution", "organisation")
    readonly_fields = ("created_at", "updated_at", "approved_at", "messages_used_today", "documents_used_today", "uploads_used_today", "monthly_messages_used", "monthly_documents_used", "monthly_uploads_used")
    fieldsets = (
        ("User and approval", {"fields": ("user", "role", "requested_role", "status", "approved_at", "approved_by", "account_expiry", "admin_notes")}),
        ("Contact and application", {"fields": ("phone", "city", "access_reason", "institution", "student_number", "organisation", "practice_area")}),
        ("Login provider", {"fields": ("auth_provider", "google_sub", "email_verified")}),
        ("Access flags", {"fields": ("can_use_civilian", "can_use_student", "can_generate_documents", "can_submit_review", "can_request_lawyer", "can_access_lawyer_portal", "can_access_admin", "can_upload_assignments", "can_use_assignment_help")}),
        ("Limits", {"fields": ("daily_message_limit", "monthly_message_limit", "daily_document_limit", "monthly_document_limit", "daily_upload_limit", "monthly_upload_limit")}),
        ("Usage", {"fields": ("usage_day", "usage_month", "messages_used_today", "documents_used_today", "uploads_used_today", "monthly_messages_used", "monthly_documents_used", "monthly_uploads_used")}),
        ("Preferences", {"fields": ("theme_preference",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ManualAccessToken)
class ManualAccessTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "last_used_at", "revoked")
    list_filter = ("revoked",)
    search_fields = ("user__email", "user__username")
    readonly_fields = ("token", "created_at", "last_used_at")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "used_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("token", "created_at", "expires_at", "used_at")
