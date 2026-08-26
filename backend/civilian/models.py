from __future__ import annotations

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class AdminNotification(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    type = models.CharField(max_length=80, default="general")
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    is_read = models.BooleanField(default=False)
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="lafre_notifications")
    related_object_type = models.CharField(max_length=80, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PlatformSetting(models.Model):
    key = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=160)
    value = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key


class LawyerBadge(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    assigned_by_admin_only = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Lawyer(models.Model):
    class ConsultationMode(models.TextChoices):
        ONLINE = "online", "Online"
        IN_PERSON = "in_person", "In person"
        BOTH = "both", "Online and in person"

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="lawyer_profile")
    full_name = models.CharField(max_length=160)
    firm_name = models.CharField(max_length=180, blank=True)
    slug = models.SlugField(max_length=220, unique=True)
    practice_areas = models.JSONField(default=list, blank=True)
    services = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    badges = models.ManyToManyField(LawyerBadge, blank=True, related_name="lawyers")
    city = models.CharField(max_length=80, blank=True)
    province = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    consultation_mode = models.CharField(max_length=20, choices=ConsultationMode.choices, default=ConsultationMode.ONLINE)
    consultation_fee_usd = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    accepts_free_legal_aid = models.BooleanField(default=False)
    available_for_appointments = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    verification_note = models.CharField(max_length=255, blank=True)
    verification_documents = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["city", "verified", "is_active"])]

    def __str__(self):
        return self.full_name


class LegalMatter(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="legal_matters")
    title = models.CharField(max_length=180)
    pathway_id = models.CharField(max_length=100, blank=True)
    issue_type = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    support_route = models.CharField(max_length=80, blank=True)
    urgency = models.CharField(max_length=30, default="normal")
    answers_json = models.JSONField(default=dict, blank=True)
    guidance_json = models.JSONField(default=dict, blank=True)
    source_count = models.PositiveIntegerField(default=0)
    grounding_status = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=40, default="open")
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["status", "issue_type", "updated_at"])]

    def __str__(self):
        return self.title


class GeneratedDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_documents")
    matter = models.ForeignKey(LegalMatter, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    document_type = models.CharField(max_length=100)
    title = models.CharField(max_length=180)
    content = models.TextField()
    template_source_note = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=40, default="draft")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class DocumentReviewRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        WAITING_ASSIGNMENT = "waiting_assignment", "Waiting assignment"
        ASSIGNED = "assigned", "Assigned"
        IN_REVIEW = "in_review", "In review"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        REVIEWED = "reviewed", "Reviewed"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="review_requests")
    document = models.ForeignKey(GeneratedDocument, on_delete=models.CASCADE, related_name="review_requests", null=True, blank=True)
    assigned_lawyer = models.ForeignKey(Lawyer, on_delete=models.SET_NULL, null=True, blank=True, related_name="document_reviews")
    review_type = models.CharField(max_length=30, default="review_only")
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.REQUESTED)
    user_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    lawyer_note = models.TextField(blank=True)
    reviewed_file = models.FileField(upload_to="lawyer_reviewed/%Y/%m/", null=True, blank=True)
    signed_or_stamped_file = models.FileField(upload_to="lawyer_signed/%Y/%m/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Review {self.id} - {self.status}"


class LawyerAssignment(models.Model):
    lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, related_name="assignments")
    matter = models.ForeignKey(LegalMatter, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    document_review = models.ForeignKey(DocumentReviewRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="lawyer_assignments_made")
    status = models.CharField(max_length=40, default="assigned")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lawyer} - {self.status}"


class AppointmentRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointment_requests")
    lawyer = models.ForeignKey(Lawyer, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointment_requests")
    matter = models.ForeignKey(LegalMatter, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    request_note = models.TextField(blank=True)
    proposed_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, default="requested")
    communication_options = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class KnowledgeBaseFailure(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="kb_failures")
    user_issue = models.TextField()
    search_query = models.TextField(blank=True)
    knowledge_base_id = models.CharField(max_length=80, blank=True)
    region = models.CharField(max_length=60, blank=True)
    source_count = models.PositiveIntegerField(default=0)
    action_needed = models.CharField(max_length=180, blank=True)
    resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PublicAnnouncement(models.Model):
    title = models.CharField(max_length=140)
    body = models.TextField()
    cta_label = models.CharField(max_length=60, blank=True)
    cta_url = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    collapsible = models.BooleanField(default=True)
    priority = models.CharField(max_length=20, default="normal")
    sort_order = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]


class PublicMatterType(models.Model):
    key = models.CharField(max_length=100, unique=True)
    letter = models.CharField(max_length=8, blank=True)
    group = models.CharField(max_length=80, blank=True)
    title = models.CharField(max_length=120)
    short_description = models.CharField(max_length=220, blank=True)
    detailed_description = models.TextField(blank=True)
    background_routing_prompt = models.TextField(blank=True)
    kb_terms = models.JSONField(default=list, blank=True)
    intake_questions = models.JSONField(default=list, blank=True)
    urgency_keywords = models.JSONField(default=list, blank=True)
    requires_location = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]


class SupportResource(models.Model):
    name = models.CharField(max_length=180)
    resource_type = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=80, blank=True)
    province = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    keywords = models.JSONField(default=list, blank=True)
    verified = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    source_note = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["resource_type", "city", "active"])]


class PathwayDocumentTemplate(models.Model):
    class MatterType(models.TextChoices):
        LENDING_MONEY = "lending_money", "Lending money"
        DEBT_RECOVERY = "debt_recovery", "Debt recovery"
        LEASE_AGREEMENT = "lease_agreement", "Lease agreement"
        AFFIDAVIT = "affidavit", "Affidavit / statement"

    class DocumentType(models.TextChoices):
        LOAN_AGREEMENT = "loan_agreement", "Loan Agreement"
        ACKNOWLEDGEMENT_OF_DEBT = "acknowledgement_of_debt", "Acknowledgement of Debt"
        REPAYMENT_PLAN = "repayment_plan", "Repayment Plan"
        DEMAND_LETTER = "demand_letter", "Demand Letter"

    matter_type = models.CharField(max_length=80, choices=MatterType.choices, default=MatterType.LENDING_MONEY)
    document_type = models.CharField(max_length=80, choices=DocumentType.choices, default=DocumentType.LOAN_AGREEMENT)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to="pathway_templates/%Y/%m/", blank=True, null=True)
    extracted_text = models.TextField(blank=True)
    support_note = models.TextField(blank=True)
    requires_practitioner_review = models.BooleanField(default=False)
    requires_certification_or_stamp = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    last_reviewed_by = models.CharField(max_length=160, blank=True)
    review_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["matter_type", "document_type", "-active", "-version"]
        indexes = [models.Index(fields=["matter_type", "document_type", "active"])]

    def __str__(self):
        return f"{self.get_matter_type_display()} - {self.get_document_type_display()} v{self.version}"


class KnowledgeBaseNote(models.Model):
    title = models.CharField(max_length=180)
    body = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    matter_type = models.CharField(max_length=80, blank=True)
    topic = models.CharField(max_length=120, blank=True)
    verified = models.BooleanField(default=True)
    visible_to_citizen = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["matter_type", "topic", "title"]

    def __str__(self):
        return self.title


class CitizenMatter(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_SIGNATURE = "pending_signature", "Pending signature"
        AWAITING_PROOFS = "awaiting_proofs", "Awaiting proofs"
        ACTIVE_REPAYMENT = "active_repayment", "Active repayment"
        REVIEW_REQUESTED = "review_requested", "Review requested"
        ASSIGNED_TO_LAWYER = "assigned_to_lawyer", "Assigned to lawyer"
        IN_REVIEW = "in_review", "In review"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        REVIEWED = "reviewed", "Reviewed"
        OVERDUE = "overdue", "Overdue"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="citizen_matters")
    matter_type = models.CharField(max_length=80, default="lending_money")
    title = models.CharField(max_length=220)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.PENDING_SIGNATURE)
    intake_json = models.JSONField(default=dict, blank=True)
    validation_json = models.JSONField(default=dict, blank=True)
    kb_support_json = models.JSONField(default=dict, blank=True)
    smart_summary_json = models.JSONField(default=dict, blank=True)
    document_template = models.ForeignKey(PathwayDocumentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    generated_document_text = models.TextField(blank=True)
    document_file = models.FileField(upload_to="citizen_generated/%Y/%m/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["matter_type", "status", "updated_at"])]

    def __str__(self):
        return self.title


class MatterPayment(models.Model):
    class Status(models.TextChoices):
        EXPECTED = "expected", "Expected"
        PENDING = "pending", "Pending"
        PART_PAID = "part_paid", "Part-paid"
        PAID = "paid", "Paid"
        LATE = "late", "Late"
        MISSED = "missed", "Missed"

    matter = models.ForeignKey(CitizenMatter, on_delete=models.CASCADE, related_name="payments")
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.EXPECTED)
    paid_date = models.DateField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    proof = models.ForeignKey("MatterAttachment", on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_payment_proof")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "id"]

    def __str__(self):
        return f"{self.currency} {self.amount} due {self.due_date}"


class MatterAttachment(models.Model):
    class Category(models.TextChoices):
        SIGNED_DOCUMENT = "signed_document", "Signed / certified / stamped document"
        PROOF_OF_LOAN = "proof_of_loan", "Proof money was given"
        BORROWER_ID = "borrower_id", "Borrower ID / identity proof"
        REPAYMENT_EVIDENCE = "repayment_evidence", "Repayment evidence"
        COLLATERAL_PROOF = "collateral_proof", "Collateral proof"
        MESSAGE_EVIDENCE = "message_evidence", "Messages about the loan"
        OTHER = "other", "Other"

    matter = models.ForeignKey(CitizenMatter, on_delete=models.CASCADE, related_name="attachments")
    payment = models.ForeignKey(MatterPayment, on_delete=models.SET_NULL, null=True, blank=True, related_name="receipts")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="matter_uploads")
    category = models.CharField(max_length=60, choices=Category.choices, default=Category.OTHER)
    title = models.CharField(max_length=180, blank=True)
    file = models.FileField(upload_to="citizen_matter_uploads/%Y/%m/")
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=["matter", "category", "uploaded_at"])]

    def __str__(self):
        return self.title or self.get_category_display()


class LegacyMatterAttachment(models.Model):
    matter = models.ForeignKey(LegalMatter, on_delete=models.CASCADE, related_name="legacy_attachments")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="legacy_matter_uploads")
    category = models.CharField(max_length=60, default="other")
    title = models.CharField(max_length=180, blank=True)
    file = models.FileField(upload_to="matter_attachments/%Y/%m/")
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
