from __future__ import annotations

import uuid
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen / Public User"
        STUDENT = "student", "Student"
        LAWYER = "lawyer", "Lawyer"
        ADMIN = "admin", "Admin"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        SUSPENDED = "suspended", "Suspended"
        REJECTED = "rejected", "Rejected"

    class AuthProvider(models.TextChoices):
        EMAIL = "email", "Email/password"
        GOOGLE = "google", "Google"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="lafre_profile")

    # Requested/primary access. Admin may later enable extra flags below.
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.CITIZEN)
    requested_role = models.CharField(max_length=30, choices=Role.choices, default=Role.CITIZEN)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)

    # Public profile/contact information.
    phone = models.CharField(max_length=60, blank=True)
    city = models.CharField(max_length=80, blank=True)
    access_reason = models.TextField(blank=True)

    # Role-specific registration details.
    institution = models.CharField(max_length=180, blank=True)
    student_number = models.CharField(max_length=80, blank=True)
    organisation = models.CharField(max_length=180, blank=True)
    practice_area = models.CharField(max_length=180, blank=True)

    # Login provider details. Google still requires Admin approval.
    auth_provider = models.CharField(max_length=30, choices=AuthProvider.choices, default=AuthProvider.EMAIL)
    google_sub = models.CharField(max_length=255, blank=True, db_index=True)
    email_verified = models.BooleanField(default=False)

    # Access flags controlled by Admin.
    can_use_civilian = models.BooleanField(default=True)
    can_use_student = models.BooleanField(default=False)
    can_generate_documents = models.BooleanField(default=False)
    can_submit_review = models.BooleanField(default=False)
    can_request_lawyer = models.BooleanField(default=False)
    can_access_lawyer_portal = models.BooleanField(default=False)
    can_access_admin = models.BooleanField(default=False)
    can_upload_assignments = models.BooleanField(default=False)
    can_use_assignment_help = models.BooleanField(default=False)

    # Resource limits controlled by Admin.
    daily_message_limit = models.PositiveIntegerField(default=0)
    monthly_message_limit = models.PositiveIntegerField(default=0)
    daily_document_limit = models.PositiveIntegerField(default=0)
    monthly_document_limit = models.PositiveIntegerField(default=0)
    daily_upload_limit = models.PositiveIntegerField(default=0)
    monthly_upload_limit = models.PositiveIntegerField(default=0)

    # Usage counters.
    messages_used_today = models.PositiveIntegerField(default=0)
    documents_used_today = models.PositiveIntegerField(default=0)
    uploads_used_today = models.PositiveIntegerField(default=0)
    monthly_messages_used = models.PositiveIntegerField(default=0)
    monthly_documents_used = models.PositiveIntegerField(default=0)
    monthly_uploads_used = models.PositiveIntegerField(default=0)
    usage_day = models.DateField(default=date.today)
    usage_month = models.CharField(max_length=7, default="")

    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_lafre_users")
    account_expiry = models.DateField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    theme_preference = models.CharField(max_length=20, default="system", choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.role} — {self.status}"

    def refresh_usage_window(self):
        today = timezone.localdate()
        month = today.strftime("%Y-%m")
        update_fields = []
        if self.usage_day != today:
            self.usage_day = today
            self.messages_used_today = 0
            self.documents_used_today = 0
            self.uploads_used_today = 0
            update_fields += ["usage_day", "messages_used_today", "documents_used_today", "uploads_used_today"]
        if self.usage_month != month:
            self.usage_month = month
            self.monthly_messages_used = 0
            self.monthly_documents_used = 0
            self.monthly_uploads_used = 0
            update_fields += ["usage_month", "monthly_messages_used", "monthly_documents_used", "monthly_uploads_used"]
        if update_fields:
            self.save(update_fields=list(set(update_fields)))

    def is_active_for_platform(self):
        if self.status != self.Status.APPROVED:
            return False
        if self.account_expiry and self.account_expiry < timezone.localdate():
            return False
        return True

    def remaining_messages(self):
        self.refresh_usage_window()
        if self.daily_message_limit <= 0:
            return 0
        return max(self.daily_message_limit - self.messages_used_today, 0)

    def remaining_documents(self):
        self.refresh_usage_window()
        if self.daily_document_limit <= 0:
            return 0
        return max(self.daily_document_limit - self.documents_used_today, 0)

    def remaining_uploads(self):
        self.refresh_usage_window()
        if self.daily_upload_limit <= 0:
            return 0
        return max(self.daily_upload_limit - self.uploads_used_today, 0)

    def consume_message(self):
        self.refresh_usage_window()
        self.messages_used_today += 1
        self.monthly_messages_used += 1
        self.save(update_fields=["messages_used_today", "monthly_messages_used", "usage_day", "usage_month"])

    def consume_document(self):
        self.refresh_usage_window()
        self.documents_used_today += 1
        self.monthly_documents_used += 1
        self.save(update_fields=["documents_used_today", "monthly_documents_used", "usage_day", "usage_month"])

    def consume_upload(self):
        self.refresh_usage_window()
        self.uploads_used_today += 1
        self.monthly_uploads_used += 1
        self.save(update_fields=["uploads_used_today", "monthly_uploads_used", "usage_day", "usage_month"])


class ManualAccessToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lafre_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token for {self.user.username}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lafre_password_reset_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=2)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at >= timezone.now()

    def __str__(self):
        return f"Password reset for {self.user.email}"
