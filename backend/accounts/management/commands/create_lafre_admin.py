from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import UserProfile
from accounts.serializers import DEFAULT_LIMITS, ROLE_TO_FLAGS


class Command(BaseCommand):
    help = "Create or update a manually managed LAFRE admin account."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--name", default="LAFRE Admin")
        parser.add_argument("--staff", action="store_true", help="Also mark the Django user as staff.")
        parser.add_argument("--superuser", action="store_true", help="Also mark the Django user as superuser.")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        if not email:
            raise CommandError("Email is required.")
        first, *rest = options["name"].strip().split()
        user, created = User.objects.get_or_create(username=email, defaults={"email": email})
        user.email = email
        user.first_name = first or "LAFRE"
        user.last_name = " ".join(rest) or "Admin"
        user.is_staff = bool(options["staff"] or options["superuser"])
        user.is_superuser = bool(options["superuser"])
        user.set_password(options["password"])
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        for key, value in ROLE_TO_FLAGS[UserProfile.Role.ADMIN].items():
            setattr(profile, key, value)
        for key, value in DEFAULT_LIMITS[UserProfile.Role.ADMIN].items():
            setattr(profile, key, value)
        profile.role = UserProfile.Role.ADMIN
        profile.requested_role = UserProfile.Role.ADMIN
        profile.status = UserProfile.Status.APPROVED
        profile.approved_at = profile.approved_at or timezone.now()
        profile.save()
        self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} LAFRE admin: {email}"))
