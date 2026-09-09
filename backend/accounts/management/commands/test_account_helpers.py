from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify

from accounts.models import UserProfile
from accounts.serializers import DEFAULT_LIMITS, ROLE_TO_FLAGS, split_name
from civilian.models import Lawyer
from forum.models import LawyerProfile as ForumLawyerProfile

TEST_PASSWORD = "TestPass!2026"


def create_test_account(*, email, name, role, password=TEST_PASSWORD):
    first_name, last_name = split_name(name)
    with transaction.atomic():
        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = role == UserProfile.Role.ADMIN
        user.is_superuser = False
        user.set_password(password)
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.requested_role = role
        profile.status = UserProfile.Status.APPROVED
        profile.email_verified = True
        profile.approved_by = None
        profile.can_use_civilian = role in {UserProfile.Role.CITIZEN, UserProfile.Role.LAWYER}
        profile.can_use_student = role == UserProfile.Role.STUDENT
        profile.can_generate_documents = role == UserProfile.Role.CITIZEN
        profile.can_submit_review = role == UserProfile.Role.LAWYER
        profile.can_request_lawyer = role == UserProfile.Role.CITIZEN
        profile.can_access_lawyer_portal = role == UserProfile.Role.LAWYER
        profile.can_access_admin = role == UserProfile.Role.ADMIN
        profile.can_upload_assignments = role == UserProfile.Role.STUDENT
        profile.can_use_assignment_help = role == UserProfile.Role.STUDENT
        for key, value in ROLE_TO_FLAGS[role].items():
            setattr(profile, key, value)
        for key, value in DEFAULT_LIMITS[role].items():
            setattr(profile, key, value)
        profile.save()

        if role == UserProfile.Role.LAWYER:
            slug = f"test-{slugify(name)}"
            lawyer, _ = Lawyer.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": name,
                    "firm_name": "Test Legal Practice",
                    "slug": slug,
                    "practice_areas": ["Family law", "Contracts and agreements"],
                    "services": ["Legal consultations", "Document review", "Mediation guidance"],
                    "languages": ["English", "Shona"],
                    "city": "Harare",
                    "province": "Harare",
                    "address": "Test office, Harare",
                    "email": email,
                    "phone": "+263 77 000 9000",
                    "years_experience": 8,
                    "consultation_mode": Lawyer.ConsultationMode.BOTH,
                    "consultation_fee_usd": 20,
                    "accepts_free_legal_aid": True,
                    "available_for_appointments": True,
                    "verified": True,
                    "verification_note": "Test account for development only.",
                    "bio": "Test lawyer profile for integration testing.",
                    "is_active": True,
                },
            )
            ForumLawyerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "slug": slug,
                    "firm_name": lawyer.firm_name,
                    "practice_area": "Family law and contracts",
                    "location": "Harare",
                    "years_experience": 8,
                    "bio": "Test forum lawyer profile for integration testing.",
                    "phone": lawyer.phone,
                    "public_email": email,
                    "verified": True,
                    "mentorship_available": True,
                },
            )
    return user
