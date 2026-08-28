from __future__ import annotations

import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import UserProfile


DEFAULT_LIMITS = {
    UserProfile.Role.STUDENT: {
        "daily_message_limit": 30,
        "monthly_message_limit": 600,
        "daily_upload_limit": 5,
        "monthly_upload_limit": 50,
        "daily_document_limit": 10,
        "monthly_document_limit": 100,
    },
    UserProfile.Role.CITIZEN: {
        "daily_message_limit": 0,
        "monthly_message_limit": 0,
        "daily_upload_limit": 10,
        "monthly_upload_limit": 120,
        "daily_document_limit": 5,
        "monthly_document_limit": 50,
    },
    UserProfile.Role.LAWYER: {
        "daily_message_limit": 0,
        "monthly_message_limit": 0,
        "daily_upload_limit": 10,
        "monthly_upload_limit": 120,
        "daily_document_limit": 10,
        "monthly_document_limit": 100,
    },
    UserProfile.Role.ADMIN: {
        "daily_message_limit": 0,
        "monthly_message_limit": 0,
        "daily_upload_limit": 0,
        "monthly_upload_limit": 0,
        "daily_document_limit": 0,
        "monthly_document_limit": 0,
    },
}

ROLE_TO_FLAGS = {
    UserProfile.Role.CITIZEN: {
        "can_use_civilian": True,
        "can_use_student": False,
        "can_generate_documents": True,
        "can_submit_review": False,
        "can_request_lawyer": True,
        "can_access_lawyer_portal": False,
        "can_access_admin": False,
        "can_upload_assignments": False,
        "can_use_assignment_help": False,
    },
    UserProfile.Role.STUDENT: {
        "can_use_civilian": False,
        "can_use_student": True,
        "can_generate_documents": False,
        "can_submit_review": False,
        "can_request_lawyer": False,
        "can_access_lawyer_portal": False,
        "can_access_admin": False,
        "can_upload_assignments": True,
        "can_use_assignment_help": True,
    },
    UserProfile.Role.LAWYER: {
        "can_use_civilian": False,
        "can_use_student": False,
        "can_generate_documents": False,
        "can_submit_review": True,
        "can_request_lawyer": False,
        "can_access_lawyer_portal": True,
        "can_access_admin": False,
        "can_upload_assignments": False,
        "can_use_assignment_help": False,
    },
    UserProfile.Role.ADMIN: {
        "can_use_civilian": False,
        "can_use_student": False,
        "can_generate_documents": False,
        "can_submit_review": True,
        "can_request_lawyer": False,
        "can_access_lawyer_portal": False,
        "can_access_admin": True,
        "can_upload_assignments": False,
        "can_use_assignment_help": False,
    },
}


def split_name(full_name: str):
    clean = (full_name or "").strip()
    if not clean:
        return "", ""
    first, *rest = clean.split()
    return first, " ".join(rest)


def module_home_for_role(role: str) -> str:
    return {
        UserProfile.Role.STUDENT: "/home",
        UserProfile.Role.CITIZEN: "/citizen/home",
        UserProfile.Role.LAWYER: "/lawyer/home",
        UserProfile.Role.ADMIN: "/admin/home",
    }.get(role, "/")


def normalise_email(value: str) -> str:
    return (value or "").strip().lower()


def email_exists(email: str) -> bool:
    clean = normalise_email(email)
    return User.objects.filter(email__iexact=clean).exists() or User.objects.filter(username__iexact=clean).exists()


def password_rule_errors(password: str) -> list[str]:
    value = password or ""
    errors: list[str] = []
    if len(value) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", value):
        errors.append("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", value):
        errors.append("Password must include a lowercase letter.")
    if not re.search(r"[0-9]", value):
        errors.append("Password must include a number.")
    if not re.search(r"[^A-Za-z0-9]", value):
        errors.append("Password must include a special character.")
    return errors


def create_lafre_user(*, email: str, password: str, first_name: str, last_name: str, role: str, phone: str = "", profile_extra: dict | None = None) -> User:
    clean_email = normalise_email(email)
    user = User.objects.create_user(
        username=clean_email,
        email=clean_email,
        password=password,
        first_name=(first_name or "").strip(),
        last_name=(last_name or "").strip(),
    )
    from django.conf import settings as django_settings
    from django.utils import timezone as django_timezone

    auto_approve = getattr(django_settings, "AUTO_APPROVE_SIGNUPS", False)
    profile_data = {
        "user": user,
        "role": role,
        "requested_role": role,
        "status": UserProfile.Status.APPROVED if auto_approve else UserProfile.Status.PENDING,
        "phone": (phone or "").strip(),
        "auth_provider": UserProfile.AuthProvider.EMAIL,
        "email_verified": auto_approve,
    }
    if auto_approve:
        profile_data["approved_at"] = django_timezone.now()
    profile_data.update(ROLE_TO_FLAGS[role])
    profile_data.update(DEFAULT_LIMITS[role])
    profile_data.update(profile_extra or {})
    UserProfile.objects.create(**profile_data)
    return user


class RegistrationStartSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages={
        "blank": "Email address is required.",
        "required": "Email address is required.",
        "invalid": "Please enter a valid email address.",
    })

    def validate_email(self, value):
        email = normalise_email(value)
        if email_exists(email):
            raise serializers.ValidationError("An account with this email already exists. Please log in or use a different email.")
        return email


class StrongPasswordMixin:
    def validate_password(self, value):
        errors = password_rule_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate_confirm_password_match(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})
        return attrs


class BaseSeparatedRegisterSerializer(StrongPasswordMixin, serializers.Serializer):
    # Backward-compatible one-shot registration serializer used by the old /register/ endpoints.
    full_name = serializers.CharField(max_length=160, error_messages={"blank": "Full name is required.", "required": "Full name is required."})
    email = serializers.EmailField(error_messages={"invalid": "Please enter a valid email address.", "blank": "Email address is required.", "required": "Email address is required."})
    password = serializers.CharField(write_only=True, min_length=8, error_messages={"blank": "Password is required.", "required": "Password is required."})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=60, required=False, allow_blank=True)

    requested_role: str = UserProfile.Role.CITIZEN

    def validate_email(self, value):
        email = normalise_email(value)
        if email_exists(email):
            raise serializers.ValidationError("An account with this email already exists. Please log in or use a different email.")
        return email

    def validate(self, attrs):
        confirm = attrs.get("confirm_password")
        if confirm and attrs.get("password") != confirm:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})
        return attrs

    def profile_kwargs(self, validated_data):
        return {}

    def create(self, validated_data):
        role = self.requested_role
        validated_data.pop("confirm_password", None)
        first, last = split_name(validated_data["full_name"])
        return create_lafre_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first,
            last_name=last,
            role=role,
            phone=validated_data.get("phone", ""),
            profile_extra=self.profile_kwargs(validated_data),
        )


class StudentRegisterSerializer(BaseSeparatedRegisterSerializer):
    # Lovable-style student registration uses only these visible fields:
    # full_name, institution (optional), email and password.
    requested_role = UserProfile.Role.STUDENT
    institution = serializers.CharField(max_length=180, required=False, allow_blank=True)

    def profile_kwargs(self, validated_data):
        return {
            "institution": validated_data.get("institution", ""),
            "student_number": "",
            "phone": "",
            "city": "",
            "access_reason": "",
        }


class CitizenRegisterSerializer(BaseSeparatedRegisterSerializer):
    requested_role = UserProfile.Role.CITIZEN
    city = serializers.CharField(max_length=80, required=False, allow_blank=True)

    def profile_kwargs(self, validated_data):
        return {"city": validated_data.get("city", ""), "access_reason": ""}


class RegisterSerializer(BaseSeparatedRegisterSerializer):
    requested_role = serializers.ChoiceField(choices=UserProfile.Role.choices, default=UserProfile.Role.CITIZEN)
    city = serializers.CharField(max_length=80, required=False, allow_blank=True)
    institution = serializers.CharField(max_length=180, required=False, allow_blank=True)
    student_number = serializers.CharField(max_length=80, required=False, allow_blank=True)
    organisation = serializers.CharField(max_length=180, required=False, allow_blank=True)
    practice_area = serializers.CharField(max_length=180, required=False, allow_blank=True)

    def create(self, validated_data):
        self.requested_role = validated_data.get("requested_role") or UserProfile.Role.CITIZEN
        return super().create(validated_data)

    def profile_kwargs(self, validated_data):
        return {
            "city": validated_data.get("city", ""),
            "institution": validated_data.get("institution", ""),
            "student_number": validated_data.get("student_number", ""),
            "organisation": validated_data.get("organisation", ""),
            "practice_area": validated_data.get("practice_area", ""),
            "access_reason": "",
        }


class StudentRegistrationCompleteSerializer(StrongPasswordMixin, serializers.Serializer):
    # Exact Lovable-style student registration form.
    full_name = serializers.CharField(max_length=160, error_messages={"blank": "Full name is required.", "required": "Full name is required."})
    institution = serializers.CharField(max_length=180, required=False, allow_blank=True)
    email = serializers.EmailField(error_messages={"invalid": "Please enter a valid email address.", "blank": "Email address is required.", "required": "Email address is required."})
    password = serializers.CharField(write_only=True, min_length=8, error_messages={"blank": "Password is required.", "required": "Password is required."})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate_email(self, value):
        email = normalise_email(value)
        if email_exists(email):
            raise serializers.ValidationError("An account with this email already exists. Please log in or use a different email.")
        return email

    def validate(self, attrs):
        confirm = attrs.get("confirm_password")
        if confirm and attrs.get("password") != confirm:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})
        return attrs

    def create(self, validated_data):
        first, last = split_name(validated_data["full_name"])
        return create_lafre_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first,
            last_name=last,
            role=UserProfile.Role.STUDENT,
            phone="",
            profile_extra={
                "institution": validated_data.get("institution", ""),
                "student_number": "",
                "city": "",
                "access_reason": "",
            },
        )


class CitizenRegistrationCompleteSerializer(StrongPasswordMixin, serializers.Serializer):
    email = serializers.EmailField(error_messages={"invalid": "Please enter a valid email address.", "blank": "Email address is required.", "required": "Email address is required."})
    full_name = serializers.CharField(max_length=160, error_messages={"blank": "Full name is required.", "required": "Full name is required."})
    phone = serializers.CharField(max_length=60, error_messages={"blank": "Phone number is required.", "required": "Phone number is required."})
    city = serializers.CharField(max_length=80, error_messages={"blank": "City or town is required.", "required": "City or town is required."})
    password = serializers.CharField(write_only=True, error_messages={"blank": "Password is required.", "required": "Password is required."})
    confirm_password = serializers.CharField(write_only=True, error_messages={"blank": "Confirm password is required.", "required": "Confirm password is required."})

    def validate_email(self, value):
        email = normalise_email(value)
        if email_exists(email):
            raise serializers.ValidationError("An account with this email already exists. Please log in or use a different email.")
        return email

    def validate(self, attrs):
        return self.validate_confirm_password_match(attrs)

    def create(self, validated_data):
        first, last = split_name(validated_data["full_name"])
        return create_lafre_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first,
            last_name=last,
            role=UserProfile.Role.CITIZEN,
            phone=validated_data.get("phone", ""),
            profile_extra={"city": validated_data.get("city", ""), "access_reason": ""},
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages={"invalid": "Please enter a valid email address.", "blank": "Email address is required.", "required": "Email address is required."})
    password = serializers.CharField(write_only=True, error_messages={"blank": "Password is required.", "required": "Password is required."})

    def validate(self, attrs):
        email = normalise_email(attrs["email"])
        user = authenticate(username=email, password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"non_field_errors": ["Incorrect email or password."]})
        attrs["user"] = user
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    credential = serializers.CharField()
    requested_role = serializers.ChoiceField(choices=UserProfile.Role.choices, required=False)
    phone = serializers.CharField(max_length=60, required=False, allow_blank=True)
    city = serializers.CharField(max_length=80, required=False, allow_blank=True)
    institution = serializers.CharField(max_length=180, required=False, allow_blank=True)
    student_number = serializers.CharField(max_length=80, required=False, allow_blank=True)
    organisation = serializers.CharField(max_length=180, required=False, allow_blank=True)
    practice_area = serializers.CharField(max_length=180, required=False, allow_blank=True)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    is_approved = serializers.SerializerMethodField()
    remaining_messages = serializers.SerializerMethodField()
    remaining_documents = serializers.SerializerMethodField()
    remaining_uploads = serializers.SerializerMethodField()
    module_home = serializers.SerializerMethodField()
    is_superuser = serializers.BooleanField(source="user.is_superuser", read_only=True)
    is_staff = serializers.BooleanField(source="user.is_staff", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id", "full_name", "email", "phone", "city", "role", "requested_role", "status", "is_approved",
            "institution", "student_number", "organisation", "practice_area", "auth_provider", "email_verified",
            "can_use_civilian", "can_use_student", "can_generate_documents", "can_submit_review", "can_request_lawyer",
            "can_access_lawyer_portal", "can_access_admin", "can_upload_assignments", "can_use_assignment_help",
            "daily_message_limit", "monthly_message_limit", "daily_document_limit", "monthly_document_limit",
            "daily_upload_limit", "monthly_upload_limit", "remaining_messages", "remaining_documents", "remaining_uploads",
            "messages_used_today", "documents_used_today", "uploads_used_today", "monthly_messages_used",
            "monthly_documents_used", "monthly_uploads_used", "theme_preference", "account_expiry", "admin_notes",
            "module_home", "created_at", "updated_at", "is_superuser", "is_staff",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_is_approved(self, obj):
        return obj.is_active_for_platform()

    def get_remaining_messages(self, obj):
        return obj.remaining_messages()

    def get_remaining_documents(self, obj):
        return obj.remaining_documents()

    def get_remaining_uploads(self, obj):
        return obj.remaining_uploads()

    def get_module_home(self, obj):
        return module_home_for_role(obj.role)
