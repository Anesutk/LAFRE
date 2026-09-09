from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q

from .models import UserProfile


def _frontend_url(path: str) -> str:
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    return f"{base}{path}"


def _from_email() -> str:
    return getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@lafre.local")


def get_admin_emails() -> list[str]:
    """Who should receive "please verify this account" emails.

    Prefers an explicit ADMIN_NOTIFICATION_EMAILS env var (comma separated)
    so deployments can route these to a shared inbox. Otherwise falls back
    to every Django staff/superuser account plus any LAFRE profile that has
    been granted admin access, which mirrors accounts.auth.is_admin_user.
    """
    configured = [
        email.strip()
        for email in getattr(settings, "ADMIN_NOTIFICATION_EMAILS", "").split(",")
        if email.strip()
    ]
    if configured:
        return configured

    admins = (
        User.objects.filter(
            Q(is_superuser=True)
            | Q(is_staff=True)
            | Q(
                lafre_profile__can_access_admin=True,
                lafre_profile__status=UserProfile.Status.APPROVED,
            )
        )
        .exclude(email="")
        .values_list("email", flat=True)
        .distinct()
    )
    return list(admins)


def module_label(role: str) -> str:
    return {
        UserProfile.Role.STUDENT: "Student",
        UserProfile.Role.CITIZEN: "Citizen",
        UserProfile.Role.LAWYER: "Lawyer",
        UserProfile.Role.ADMIN: "Admin",
    }.get(role, "User")


def send_admin_verification_email(user: User, profile: UserProfile) -> bool:
    """Emails LAFRE admins that a new account is waiting for approval.

    Returns True if an email send was attempted (i.e. there was at least
    one admin recipient), False otherwise, so callers can decide whether to
    fall back to the in-app notification only.
    """
    recipients = get_admin_emails()
    if not recipients:
        return False

    label = module_label(profile.role)
    review_link = _frontend_url("/admin")
    name = user.get_full_name() or user.email

    subject = f"LAFRE: new {label} account awaiting verification"
    body = (
        f"{name} ({user.email}) has requested {label} access on LAFRE.\n\n"
        f"Sign in to the admin dashboard to review and approve or reject this request:\n"
        f"{review_link}\n\n"
        "This is an automated verification notice."
    )
    send_mail(subject, body, _from_email(), recipients, fail_silently=True)
    return True


def send_account_approved_email(user: User, profile: UserProfile) -> bool:
    """Emails a user once an admin has approved their account."""
    if not user.email:
        return False

    label = module_label(profile.role)
    login_link = _frontend_url("/login")
    first_name = user.first_name or (user.get_full_name() or "there")

    subject = "Your LAFRE account has been approved"
    body = (
        f"Hi {first_name},\n\n"
        f"Good news — your LAFRE {label} account has been verified and approved by an "
        f"administrator. You can now sign in:\n{login_link}\n\n"
        "Welcome to LAFRE."
    )
    send_mail(subject, body, _from_email(), [user.email], fail_silently=True)
    return True


def send_account_rejected_email(user: User, profile: UserProfile) -> bool:
    """Emails a user if an admin rejects their account request."""
    if not user.email:
        return False

    label = module_label(profile.role)
    subject = "Your LAFRE account request was not approved"
    body = (
        f"Hi {user.first_name or 'there'},\n\n"
        f"Your LAFRE {label} account request was reviewed by an administrator and was not "
        "approved. If you believe this is a mistake, please contact LAFRE support.\n\n"
        "— LAFRE"
    )
    send_mail(subject, body, _from_email(), [user.email], fail_silently=True)
    return True
