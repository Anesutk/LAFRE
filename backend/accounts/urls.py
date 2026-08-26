from django.urls import path

from .views import (
    AdminApproveUserView,
    AdminLoginView,
    CitizenLoginView,
    CitizenRegisterCompleteView,
    CitizenRegisterStartView,
    CitizenRegisterView,
    GoogleAuthView,
    LawyerLoginView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    StudentLoginView,
    StudentRegisterCompleteView,
    StudentRegisterStartView,
    StudentRegisterView,
)
from .admin_views import AdminDashboardView, AdminUserDetailView, AdminUserQuickApproveView, AdminUsersView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="lafre-register"),
    path("login/", LoginView.as_view(), name="lafre-login"),

    # New step-based registration endpoints used by the redesigned Next.js auth screens.
    path("student/register/start/", StudentRegisterStartView.as_view(), name="lafre-student-register-start"),
    path("student/register/complete/", StudentRegisterCompleteView.as_view(), name="lafre-student-register-complete"),
    path("citizen/register/start/", CitizenRegisterStartView.as_view(), name="lafre-citizen-register-start"),
    path("citizen/register/complete/", CitizenRegisterCompleteView.as_view(), name="lafre-citizen-register-complete"),

    # Backward-compatible one-shot registration endpoints.
    path("student/register/", StudentRegisterView.as_view(), name="lafre-student-register"),
    path("citizen/register/", CitizenRegisterView.as_view(), name="lafre-citizen-register"),

    path("student/login/", StudentLoginView.as_view(), name="lafre-student-login"),
    path("citizen/login/", CitizenLoginView.as_view(), name="lafre-citizen-login"),
    path("lawyer/login/", LawyerLoginView.as_view(), name="lafre-lawyer-login"),
    path("admin/login/", AdminLoginView.as_view(), name="lafre-admin-login"),
    path("logout/", LogoutView.as_view(), name="lafre-logout"),
    path("me/", MeView.as_view(), name="lafre-me"),
    path("google/", GoogleAuthView.as_view(), name="lafre-google-auth"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="lafre-password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="lafre-password-reset-confirm"),
    path("admin/users/<int:user_id>/approve/", AdminApproveUserView.as_view(), name="lafre-admin-approve-user"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="lafre-admin-dashboard"),
    path("admin/users/", AdminUsersView.as_view(), name="lafre-admin-users"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="lafre-admin-user-detail"),
    path("admin/users/<int:user_id>/quick-approve/", AdminUserQuickApproveView.as_view(), name="lafre-admin-user-quick-approve"),
]
