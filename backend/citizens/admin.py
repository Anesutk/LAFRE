from django.contrib import admin
from .models import CitizenProfile, Matter, GeneratedDocument, MatterEvidence, LawyerReviewRequest, SimulatedPayment

@admin.register(CitizenProfile)
class CitizenProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone')

@admin.register(Matter)
class MatterAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'pathway_title', 'status', 'risk_level', 'updated_at')
    list_filter = ('status', 'pathway_key', 'risk_level')
    search_fields = ('title', 'summary', 'user__email')

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('matter', 'document_type', 'version', 'created_at')

@admin.register(MatterEvidence)
class MatterEvidenceAdmin(admin.ModelAdmin):
    list_display = ('matter', 'evidence_type', 'description', 'created_at')

@admin.register(LawyerReviewRequest)
class LawyerReviewRequestAdmin(admin.ModelAdmin):
    list_display = ('matter', 'review_type', 'fixed_fee', 'payment_status', 'review_status', 'created_at')

@admin.register(SimulatedPayment)
class SimulatedPaymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'review_request', 'provider', 'amount', 'status', 'created_at')
