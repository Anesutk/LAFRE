from django.conf import settings
from django.db import models
from django.utils import timezone


class CitizenProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='citizen_profile')
    phone = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.get_full_name() or self.user.email or self.user.username


class Matter(models.Model):
    STATUS_CHOICES = [
        ('collecting_info', 'Collecting information'),
        ('document_generated', 'Document generated'),
        ('needs_review', 'Needs review'),
        ('sent_to_lawyer', 'Sent to lawyer'),
        ('reviewed', 'Reviewed'),
        ('ready_to_sign', 'Ready to sign'),
        ('signed', 'Signed'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='citizen_pathway_matters')
    pathway_key = models.CharField(max_length=80)
    pathway_title = models.CharField(max_length=120)
    title = models.CharField(max_length=180)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='collecting_info')
    risk_level = models.CharField(max_length=40, default='Medium')
    summary = models.TextField(blank=True)
    next_steps = models.JSONField(default=list, blank=True)
    flags = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class GeneratedDocument(models.Model):
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=80)
    version = models.PositiveIntegerField(default=1)
    content = models.TextField()
    pdf_file = models.FileField(upload_to='citizen_documents/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.matter.title} v{self.version}'


class MatterEvidence(models.Model):
    EVIDENCE_TYPES = [
        ('id', 'ID document'),
        ('proof_of_payment', 'Proof of payment'),
        ('receipt', 'Receipt'),
        ('screenshot', 'Screenshot'),
        ('signed_document', 'Signed document'),
        ('collateral_photo', 'Collateral photo'),
        ('other', 'Other'),
    ]

    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name='evidence')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    evidence_type = models.CharField(max_length=40, choices=EVIDENCE_TYPES, default='other')
    description = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='citizen_evidence/')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.matter.title} evidence'


class LawyerReviewRequest(models.Model):
    REVIEW_TYPES = [
        ('document_check', 'Document check'),
        ('certification', 'Certification / validation'),
        ('consultation', 'Consultation request'),
    ]
    REVIEW_STATUS = [
        ('draft', 'Draft'),
        ('payment_pending', 'Payment pending'),
        ('submitted', 'Submitted'),
        ('assigned', 'Assigned'),
        ('reviewed', 'Reviewed'),
        ('cancelled', 'Cancelled'),
    ]

    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name='review_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review_type = models.CharField(max_length=40, choices=REVIEW_TYPES, default='document_check')
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=3.00)
    payment_status = models.CharField(max_length=30, default='pending')
    review_status = models.CharField(max_length=30, choices=REVIEW_STATUS, default='payment_pending')
    mock_lawyer_name = models.CharField(max_length=120, default='LAFRE Review Desk')
    lawyer_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class SimulatedPayment(models.Model):
    review_request = models.ForeignKey(LawyerReviewRequest, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=40, default='EcoCash Simulation')
    phone_number = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=30, default='success')
    created_at = models.DateTimeField(default=timezone.now)
