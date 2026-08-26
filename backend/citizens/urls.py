from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register_view),
    path('auth/login/', views.login_view),
    path('auth/me/', views.me_view),
    path('pathways/', views.pathways_view),
    path('pathways/<str:key>/', views.pathway_detail_view),
    path('matters/', views.MatterListCreateView.as_view()),
    path('matters/<int:pk>/', views.MatterDetailView.as_view()),
    path('matters/<int:pk>/generate-document/', views.generate_document_view),
    path('documents/<int:document_id>/download-pdf/', views.download_pdf_view),
    path('matters/<int:pk>/evidence/', views.upload_evidence_view),
    path('matters/<int:pk>/request-review/', views.request_review_view),
    path('reviews/<int:review_id>/simulate-payment/', views.simulate_payment_view),
    path('matters/<int:pk>/ask/', views.ask_matter_view),
]
