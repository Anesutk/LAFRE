from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from .models import ManualAccessToken

TOKEN_INACTIVITY_DAYS = 30


def get_user_from_request(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token_value = header.replace("Bearer ", "", 1).strip()
    if not token_value:
        return None
    try:
        token = ManualAccessToken.objects.select_related("user", "user__lafre_profile").get(token=token_value, revoked=False)
    except ManualAccessToken.DoesNotExist:
        return None
    last_activity = token.last_used_at or token.created_at
    if last_activity < timezone.now() - timedelta(days=TOKEN_INACTIVITY_DAYS):
        token.revoked = True
        token.save(update_fields=["revoked"])
        return None
    # Avoid a write on every polling/chat request while still keeping inactivity expiry accurate.
    if not token.last_used_at or token.last_used_at < timezone.now() - timedelta(hours=1):
        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])
    return token.user


def get_profile_from_request(request):
    user = get_user_from_request(request)
    if not user:
        return None
    return getattr(user, "lafre_profile", None)


def is_admin_user(user):
    if not user:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, "lafre_profile", None)
    return bool(profile and profile.can_access_admin and profile.status == "approved")
