from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import get_user_from_request, is_admin_user
from .models import ManualAccessToken, PasswordResetToken, UserProfile
from .serializers import (
    CitizenRegisterSerializer,
    CitizenRegistrationCompleteSerializer,
    GoogleAuthSerializer,
    LoginSerializer,
    RegisterSerializer,
    RegistrationStartSerializer,
    StudentRegisterSerializer,
    StudentRegistrationCompleteSerializer,
    UserProfileSerializer,
    module_home_for_role,
)

try:
    from civilian.models import AdminNotification
except Exception:  # pragma: no cover
    AdminNotification = None


def create_admin_notification(title: str, message: str, *, type: str = "system", priority: str = "medium", related_user=None, metadata=None):
    if not AdminNotification:
        return
    try:
        AdminNotification.objects.create(
            title=title,
            message=message,
            type=type,
            priority=priority,
            related_user=related_user,
            metadata=metadata or {},
        )
    except Exception:
        pass


def normalise_error_value(value):
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return {key: normalise_error_value(val) for key, val in value.items()}
    return [str(value)]


def normalise_serializer_errors(errors) -> dict:
    if not isinstance(errors, dict):
        return {"non_field_errors": normalise_error_value(errors)}
    output = {}
    for key, value in errors.items():
        output[key] = normalise_error_value(value)
    return output


def api_error(message: str, *, errors=None, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({
        "ok": False,
        "success": False,
        "message": message,
        "detail": message,
        "errors": normalise_serializer_errors(errors or {}),
    }, status=http_status)


def make_token_response(user: User):
    token = ManualAccessToken.objects.create(user=user)
    profile = getattr(user, "lafre_profile", None)
    return {
        "ok": True,
        "success": True,
        "token": str(token.token),
        "profile": UserProfileSerializer(profile).data if profile else None,
    }


def suggested_redirect(profile: UserProfile | None, requested_module: str | None = None):
    if not profile:
        return "/login"
    if not profile.is_active_for_platform():
        return "/pending" if requested_module in {"student", "citizen", "lawyer", "admin"} else "/pending-approval"
    if requested_module == "student":
        return "/chat" if profile.can_use_student else "/access-denied"
    if requested_module == "citizen":
        return "/citizen/home" if profile.can_use_civilian else "/access-denied"
    if requested_module == "lawyer":
        return "/lawyer/home" if profile.can_access_lawyer_portal else "/access-denied"
    if requested_module == "admin":
        return "/admin/home" if (profile.can_access_admin or profile.user.is_staff or profile.user.is_superuser) else "/access-denied"
    return module_home_for_role(profile.role)


def module_label(role: str) -> str:
    return {
        UserProfile.Role.STUDENT: "Student",
        UserProfile.Role.CITIZEN: "Citizen",
        UserProfile.Role.LAWYER: "Lawyer",
        UserProfile.Role.ADMIN: "Admin",
    }.get(role, "User")


class ModuleRegisterStartView(APIView):
    authentication_classes = []
    permission_classes = []
    role = UserProfile.Role.CITIZEN

    def post(self, request):
        serializer = RegistrationStartSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error("Please fix the highlighted fields.", errors=serializer.errors)
        return Response({
            "ok": True,
            "success": True,
            "message": "Email looks good. Continue to the next step.",
            "email": serializer.validated_data["email"],
            "next_step": "details",
        })


class StudentRegisterStartView(ModuleRegisterStartView):
    role = UserProfile.Role.STUDENT


class CitizenRegisterStartView(ModuleRegisterStartView):
    role = UserProfile.Role.CITIZEN


class ModuleRegisterCompleteView(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = CitizenRegistrationCompleteSerializer
    role = UserProfile.Role.CITIZEN

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return api_error("Please fix the highlighted fields.", errors=serializer.errors)
        user = serializer.save()
        profile = user.lafre_profile
        label = module_label(profile.role)
        create_admin_notification(
            f"New {profile.role} registration",
            f"{user.get_full_name() or user.email} requested {label} access.",
            type="user_registration",
            priority="medium",
            related_user=user,
            metadata={"module": profile.role},
        )
        return Response({
            "ok": True,
            "success": True,
            "message": f"Your LAFRE {label} account request was submitted for administrator approval.",
            "profile": UserProfileSerializer(profile).data,
            "redirect_to": (
                "/chat" if profile.role == "student" and getattr(settings, "AUTO_APPROVE_SIGNUPS", False)
                else "/pending" if profile.role in {"student", "citizen"}
                else "/pending-approval"
            ),
        }, status=status.HTTP_201_CREATED)


class StudentRegisterCompleteView(ModuleRegisterCompleteView):
    serializer_class = StudentRegistrationCompleteSerializer
    role = UserProfile.Role.STUDENT


class CitizenRegisterCompleteView(ModuleRegisterCompleteView):
    serializer_class = CitizenRegistrationCompleteSerializer
    role = UserProfile.Role.CITIZEN


class ModuleRegisterView(APIView):
    # Backward-compatible one-shot registration endpoint.
    authentication_classes = []
    permission_classes = []
    serializer_class = RegisterSerializer
    module = "general"

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return api_error("Please fix the highlighted fields.", errors=serializer.errors)
        user = serializer.save()
        profile = user.lafre_profile
        label = module_label(profile.role)
        create_admin_notification(
            f"New {profile.role} registration",
            f"{user.get_full_name() or user.email} requested {label} access.",
            type="user_registration",
            priority="medium",
            related_user=user,
            metadata={"module": profile.role},
        )
        return Response({
            "ok": True,
            "success": True,
            "message": f"Your LAFRE {label} account request was submitted for administrator approval.",
            "profile": UserProfileSerializer(profile).data,
            "redirect_to": (
                "/chat" if profile.role == "student" and getattr(settings, "AUTO_APPROVE_SIGNUPS", False)
                else "/pending" if profile.role in {"student", "citizen"}
                else "/pending-approval"
            ),
        }, status=status.HTTP_201_CREATED)


class StudentRegisterView(ModuleRegisterView):
    serializer_class = StudentRegisterSerializer
    module = "student"


class CitizenRegisterView(ModuleRegisterView):
    serializer_class = CitizenRegisterSerializer
    module = "citizen"


class RegisterView(ModuleRegisterView):
    serializer_class = RegisterSerializer
    module = "general"


class ModuleLoginView(APIView):
    authentication_classes = []
    permission_classes = []
    required_module: str | None = None

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            errors = normalise_serializer_errors(serializer.errors)
            if "non_field_errors" in errors:
                return api_error("We could not sign you in. Check your details and try again.", errors=errors)
            return api_error("Please fix the highlighted fields.", errors=errors)

        user = serializer.validated_data["user"]
        profile = getattr(user, "lafre_profile", None)
        if not profile:
            return api_error("This account is not configured for LAFRE access.", errors={"non_field_errors": ["Account profile not found."]}, http_status=status.HTTP_403_FORBIDDEN)

        if self.required_module == "student" and profile.role != UserProfile.Role.STUDENT and not profile.can_use_student:
            return api_error("Use a LAFRE Student account to sign in here.", errors={"email": ["This is not a student account."]}, http_status=status.HTTP_403_FORBIDDEN)
        if self.required_module == "citizen" and profile.role != UserProfile.Role.CITIZEN and not profile.can_use_civilian:
            return api_error("Use a LAFRE Citizen account to sign in here.", errors={"email": ["This is not a citizen account."]}, http_status=status.HTTP_403_FORBIDDEN)
        if self.required_module == "lawyer" and not profile.can_access_lawyer_portal:
            return api_error("This account does not have lawyer portal access.", errors={"email": ["Lawyer accounts are issued by LAFRE Admin after verification."]}, http_status=status.HTTP_403_FORBIDDEN)
        if self.required_module == "admin" and not is_admin_user(user):
            return api_error("This account does not have admin access.", errors={"email": ["Admin access is required."]}, http_status=status.HTTP_403_FORBIDDEN)
        if profile.status == UserProfile.Status.SUSPENDED:
            return api_error("This account is suspended. Contact support or an administrator.", errors={"non_field_errors": ["Account suspended."]}, http_status=status.HTTP_403_FORBIDDEN)
        if profile.status == UserProfile.Status.REJECTED:
            return api_error("This account request was rejected. Contact support if this is a mistake.", errors={"non_field_errors": ["Account rejected."]}, http_status=status.HTTP_403_FORBIDDEN)

        payload = make_token_response(user)
        payload["redirect_to"] = suggested_redirect(profile, self.required_module)
        return Response(payload)


class LoginView(ModuleLoginView):
    required_module = None


class StudentLoginView(ModuleLoginView):
    required_module = "student"


class CitizenLoginView(ModuleLoginView):
    required_module = "citizen"


class LawyerLoginView(ModuleLoginView):
    required_module = "lawyer"


class AdminLoginView(ModuleLoginView):
    required_module = "admin"


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"ok": True})
        token_value = request.headers.get("Authorization", "").replace("Bearer ", "", 1).strip()
        if token_value:
            ManualAccessToken.objects.filter(user=user, token=token_value).update(revoked=True)
        return Response({"ok": True})


class MeView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_user_from_request(request)
        if not user:
            return api_error("Not authenticated.", errors={"non_field_errors": ["Not authenticated."]}, http_status=status.HTTP_401_UNAUTHORIZED)
        profile = user.lafre_profile
        module = request.query_params.get("module")
        return Response({"ok": True, "profile": UserProfileSerializer(profile).data, "redirect_to": suggested_redirect(profile, module)})


class GoogleAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        return api_error(
            "Google sign-in is disabled until Google client IDs are configured and approved.",
            errors={"non_field_errors": ["Google sign-in is not configured."]},
        )


class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = (request.data.get("email") or "").lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            reset = PasswordResetToken.objects.create(user=user)
            link = f"{getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')}/reset-password?token={reset.token}"
            send_mail(
                "Reset your LAFRE password",
                f"Use this link to reset your password: {link}",
                getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@lafre.local"),
                [user.email],
                fail_silently=True,
            )
            if settings.DEBUG:
                return Response({"ok": True, "message": "Reset link created.", "debug_reset_link": link, "token": str(reset.token)})
        return Response({"ok": True, "message": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        token = request.data.get("token")
        password = request.data.get("password") or ""
        if len(password) < 8:
            return api_error("Password must be at least 8 characters.", errors={"password": ["Password must be at least 8 characters."]})
        try:
            reset = PasswordResetToken.objects.select_related("user").get(token=token, used_at__isnull=True)
        except PasswordResetToken.DoesNotExist:
            return api_error("Invalid or already used reset token.", errors={"token": ["Invalid or already used reset token."]})
        if reset.expires_at < timezone.now():
            return api_error("This reset token has expired.", errors={"token": ["This reset token has expired."]})
        reset.user.set_password(password)
        reset.user.save(update_fields=["password"])
        reset.used_at = timezone.now()
        reset.save(update_fields=["used_at"])
        ManualAccessToken.objects.filter(user=reset.user).update(revoked=True)
        return Response({"ok": True, "message": "Password reset complete. Please sign in again."})
class AdminApproveUserView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, user_id: int):
        admin = get_user_from_request(request)
        if not is_admin_user(admin):
            return Response({"ok": False, "detail": "Admin access required."}, status=403)
        try:
            user = User.objects.get(id=user_id)
            profile = user.lafre_profile
        except Exception:
            return Response({"ok": False, "detail": "User not found."}, status=404)
        profile.status = UserProfile.Status.APPROVED
        profile.approved_by = admin
        profile.approved_at = timezone.now()
        profile.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
        return Response({"ok": True, "profile": UserProfileSerializer(profile).data})
