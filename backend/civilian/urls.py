from django.urls import path

from .views import (
    AdminCitizenMatterListView,
    AdminDocumentTemplateDetailView,
    AdminDocumentTemplateListCreateView,
    AdminKnowledgeBaseView,
    AdminLawyersView,
    AdminReviewQueueView,
    AttachmentDownloadView,
    AttachmentFileView,
    CitizenMatterListView,
    LendingAttachmentUploadView,
    LendingCreateMatterView,
    LendingMatterDetailView,
    MatterDocumentDownloadView,
    MatterDocumentView,
    RequestLawyerReviewView,
)
from .lawyer_views import LawyerDashboardView, LawyerReviewDetailView, LawyerReviewUploadView

urlpatterns = [
    path("citizen/matters/", CitizenMatterListView.as_view(), name="citizen-matter-list"),
    path("citizen/lending/create/", LendingCreateMatterView.as_view(), name="citizen-lending-create"),
    path("citizen/lending/matters/<int:pk>/", LendingMatterDetailView.as_view(), name="citizen-lending-detail"),
    path("citizen/lending/matters/<int:pk>/attachments/", LendingAttachmentUploadView.as_view(), name="citizen-lending-attachment"),
    path("citizen/matters/<int:pk>/review/", RequestLawyerReviewView.as_view(), name="citizen-request-lawyer-review"),
    path("citizen/matters/<int:pk>/document/view/", MatterDocumentView.as_view(), name="citizen-matter-document-view"),
    path("citizen/matters/<int:pk>/document/download/", MatterDocumentDownloadView.as_view(), name="citizen-matter-document-download"),
    path("documents/attachments/<int:pk>/view/", AttachmentFileView.as_view(), name="matter-attachment-view"),
    path("documents/attachments/<int:pk>/download/", AttachmentDownloadView.as_view(), name="matter-attachment-download"),
    path("admin/document-templates/", AdminDocumentTemplateListCreateView.as_view(), name="admin-document-templates"),
    path("admin/document-templates/<int:pk>/", AdminDocumentTemplateDetailView.as_view(), name="admin-document-template-detail"),
    path("admin/knowledge-base/", AdminKnowledgeBaseView.as_view(), name="admin-knowledge-base"),
    path("admin/citizen-matters/", AdminCitizenMatterListView.as_view(), name="admin-citizen-matters"),
    path("admin/lawyers/", AdminLawyersView.as_view(), name="admin-lawyers"),
    path("admin/reviews/", AdminReviewQueueView.as_view(), name="admin-reviews"),
    path("lawyer/dashboard/", LawyerDashboardView.as_view(), name="lawyer-dashboard"),
    path("lawyer/reviews/<int:pk>/", LawyerReviewDetailView.as_view(), name="lawyer-review-detail"),
    path("lawyer/reviews/<int:pk>/upload/", LawyerReviewUploadView.as_view(), name="lawyer-review-upload"),
]
