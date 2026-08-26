from __future__ import annotations

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import get_user_from_request, is_admin_user
from .models import UserProfile
from .serializers import DEFAULT_LIMITS, ROLE_TO_FLAGS, UserProfileSerializer


SAFE_PROFILE_FIELDS = {
    "status", "phone", "city", "institution", "student_number", "organisation", "practice_area",
    "daily_message_limit", "monthly_message_limit", "daily_document_limit", "monthly_document_limit",
    "daily_upload_limit", "monthly_upload_limit", "account_expiry", "admin_notes",
    "can_use_civilian", "can_use_student", "can_generate_documents", "can_submit_review",
    "can_request_lawyer", "can_access_lawyer_portal", "can_access_admin",
    "can_upload_assignments", "can_use_assignment_help",
}


def _admin_or_403(request):
    user = get_user_from_request(request)
    if not is_admin_user(user):
        return None, Response({"ok": False, "detail": "Admin access required."}, status=403)
    return user, None


def _require_password(request, admin_user):
    password = request.data.get("admin_password") or request.data.get("password") or ""
    if not password:
        return Response({"ok": False, "detail": "Admin password confirmation is required for this action."}, status=400)
    if not authenticate(username=admin_user.username, password=password):
        return Response({"ok": False, "detail": "Admin password confirmation failed."}, status=403)
    return None


def apply_role_preset(profile: UserProfile, role: str):
    profile.role = role
    profile.requested_role = role
    for key, value in ROLE_TO_FLAGS.get(role, {}).items():
        setattr(profile, key, value)
    for key, value in DEFAULT_LIMITS.get(role, {}).items():
        setattr(profile, key, value)


def profile_row(profile: UserProfile):
    return UserProfileSerializer(profile).data


class AdminDashboardView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin, error = _admin_or_403(request)
        if error:
            return error
        qs = UserProfile.objects.select_related("user")
        data = {
            "ok": True,
            "stats": {
                "pending_students": qs.filter(status="pending", requested_role="student").count(),
                "pending_citizens": qs.filter(status="pending", requested_role="citizen").count(),
                "approved_students": qs.filter(status="approved", role="student").count(),
                "approved_citizens": qs.filter(status="approved", role="citizen").count(),
                "lawyers": qs.filter(role="lawyer").count(),
                "suspended_users": qs.filter(status="suspended").count(),
            },
            "today_queue": [],
        }
        for profile in qs.filter(status="pending").order_by("created_at")[:8]:
            data["today_queue"].append({
                "type": f"{profile.requested_role}_request",
                "title": f"Approve {profile.get_requested_role_display()} account",
                "user_id": profile.user_id,
                "name": profile.user.get_full_name() or profile.user.email,
                "email": profile.user.email,
                "created_at": profile.created_at,
            })
        return Response(data)


class AdminUsersView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin, error = _admin_or_403(request)
        if error:
            return error
        role = request.query_params.get("role")
        status = request.query_params.get("status")
        q = (request.query_params.get("q") or "").strip()
        qs = UserProfile.objects.select_related("user").all()
        if role:
            qs = qs.filter(role=role) | qs.filter(requested_role=role)
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(user__email__icontains=q) | qs.filter(user__first_name__icontains=q) | qs.filter(user__last_name__icontains=q)
        return Response({"ok": True, "users": [profile_row(p) for p in qs.order_by("-created_at")[:250]]})


class AdminUserDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_profile(self, user_id):
        try:
            return UserProfile.objects.select_related("user", "approved_by").get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None

    def get(self, request, user_id: int):
        admin, error = _admin_or_403(request)
        if error:
            return error
        profile = self.get_profile(user_id)
        if not profile:
            return Response({"ok": False, "detail": "User not found."}, status=404)
        return Response({"ok": True, "profile": profile_row(profile)})

    def patch(self, request, user_id: int):
        admin, error = _admin_or_403(request)
        if error:
            return error
        sensitive = {"status", "can_access_admin", "can_access_lawyer_portal", "daily_message_limit", "monthly_message_limit", "daily_upload_limit", "monthly_upload_limit"}
        if any(field in request.data for field in sensitive):
            password_error = _require_password(request, admin)
            if password_error:
                return password_error
        profile = self.get_profile(user_id)
        if not profile:
            return Response({"ok": False, "detail": "User not found."}, status=404)
        role_preset = request.data.get("role_preset")
        if role_preset in ROLE_TO_FLAGS:
            apply_role_preset(profile, role_preset)
        for field in SAFE_PROFILE_FIELDS:
            if field in request.data:
                setattr(profile, field, request.data[field])
        if profile.status == UserProfile.Status.APPROVED and not profile.approved_at:
            profile.approved_at = timezone.now()
            profile.approved_by = admin
        profile.save()
        return Response({"ok": True, "profile": profile_row(profile)})


class AdminUserQuickApproveView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, user_id: int):
        admin, error = _admin_or_403(request)
        if error:
            return error
        password_error = _require_password(request, admin)
        if password_error:
            return password_error
        try:
            profile = UserProfile.objects.select_related("user").get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"ok": False, "detail": "User not found."}, status=404)
        apply_role_preset(profile, profile.requested_role or profile.role)
        profile.status = UserProfile.Status.APPROVED
        profile.approved_by = admin
        profile.approved_at = timezone.now()
        profile.save()
        return Response({"ok": True, "profile": profile_row(profile)})
