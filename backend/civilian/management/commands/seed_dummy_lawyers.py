from decimal import Decimal
from django.core.management.base import BaseCommand
from civilian.models import Lawyer, LawyerReview


DUMMY_LAWYERS = [
    {
        "full_name": "Tariro Moyo Demo",
        "firm_name": "Moyo & Partners Demo Chambers",
        "practice_areas": ["property", "contracts", "civil"],
        "services": ["Tenant disputes", "Property transfer guidance", "Demand letters"],
        "languages": ["English", "Shona"],
        "city": "Harare",
        "province": "Harare",
        "address": "Demo Office, Harare CBD",
        "email": "tariro.demo@example.com",
        "phone": "+263 77 000 1001",
        "years_experience": 9,
        "rating": Decimal("4.80"),
        "review_count": 42,
        "consultation_mode": "hybrid",
        "consultation_fee_usd": Decimal("25.00"),
        "accepts_online_consultations": True,
        "available_for_appointments": True,
        "verified": False,
        "verification_note": "Fictional demo data - not a real lawyer",
        "bio": "Demo profile for property, tenancy, contracts and civil disputes.",
    },
    {
        "full_name": "Nyasha Dube Demo",
        "firm_name": "Dube Family Law Demo Practice",
        "practice_areas": ["family", "estates", "civil"],
        "services": ["Divorce consultation", "Maintenance guidance", "Wills and estates"],
        "languages": ["English", "Ndebele", "Shona"],
        "city": "Bulawayo",
        "province": "Bulawayo",
        "address": "Demo Office, Bulawayo CBD",
        "email": "nyasha.demo@example.com",
        "phone": "+263 77 000 1002",
        "years_experience": 12,
        "rating": Decimal("4.70"),
        "review_count": 35,
        "consultation_mode": "hybrid",
        "consultation_fee_usd": Decimal("20.00"),
        "accepts_online_consultations": True,
        "available_for_appointments": True,
        "verified": False,
        "verification_note": "Fictional demo data - not a real lawyer",
        "bio": "Demo profile for family law, maintenance, divorce and estate planning.",
    },
    {
        "full_name": "Farai Chikomo Demo",
        "firm_name": "Chikomo Labour & Employment Demo Legal",
        "practice_areas": ["employment", "contracts", "civil"],
        "services": ["Unfair dismissal", "Employment contracts", "Salary disputes"],
        "languages": ["English", "Shona"],
        "city": "Gweru",
        "province": "Midlands",
        "address": "Demo Office, Gweru",
        "email": "farai.demo@example.com",
        "phone": "+263 77 000 1003",
        "years_experience": 7,
        "rating": Decimal("4.60"),
        "review_count": 28,
        "consultation_mode": "online",
        "consultation_fee_usd": Decimal("15.00"),
        "accepts_online_consultations": True,
        "available_for_appointments": True,
        "verified": False,
        "verification_note": "Fictional demo data - not a real lawyer",
        "bio": "Demo profile for employment, dismissal and workplace contract issues.",
    },
    {
        "full_name": "Rudo Ndlovu Demo",
        "firm_name": "Ndlovu Criminal Defence Demo Chambers",
        "practice_areas": ["criminal", "human_rights", "civil"],
        "services": ["Bail guidance", "Police rights information", "Court representation referral"],
        "languages": ["English", "Ndebele"],
        "city": "Bulawayo",
        "province": "Bulawayo",
        "address": "Demo Office, Bulawayo",
        "email": "rudo.demo@example.com",
        "phone": "+263 77 000 1004",
        "years_experience": 11,
        "rating": Decimal("4.90"),
        "review_count": 51,
        "consultation_mode": "office",
        "consultation_fee_usd": Decimal("30.00"),
        "accepts_online_consultations": False,
        "available_for_appointments": True,
        "verified": False,
        "verification_note": "Fictional demo data - not a real lawyer",
        "bio": "Demo profile for criminal defence and rights-related matters.",
    },
    {
        "full_name": "Kudzai Manyika Demo",
        "firm_name": "Manyika Business Law Demo Advisory",
        "practice_areas": ["business", "contracts", "consumer"],
        "services": ["Company registration guidance", "Business contracts", "Debt letters"],
        "languages": ["English", "Shona"],
        "city": "Harare",
        "province": "Harare",
        "address": "Demo Office, Avondale",
        "email": "kudzai.demo@example.com",
        "phone": "+263 77 000 1005",
        "years_experience": 8,
        "rating": Decimal("4.50"),
        "review_count": 22,
        "consultation_mode": "online",
        "consultation_fee_usd": Decimal("18.00"),
        "accepts_online_consultations": True,
        "available_for_appointments": True,
        "verified": False,
        "verification_note": "Fictional demo data - not a real lawyer",
        "bio": "Demo profile for company, contract, small business and debt matters.",
    },
    {
        "full_name": "Memory Sibanda Demo",
        "firm_name": "Sibanda Estates Demo Legal",
        "practice_areas": ["estates", "family", "property"],
        "services": ["Deceased estates", "Wills guidance", "Inheritance disputes"],
        "languages": ["English", "Ndebele"],
        "city": "Gweru",
        "province": "Midlands",
        "address": "Demo Office, Gweru CBD",
        "email": "memory.demo@example.com",
        "phone": "+263 77 000 1006",
        "years_experience": 10,
        "rating": Decimal("4.75"),
        "review_count": 31,
        "consultation_mode": "hybrid",
        "consultation_fee_usd": Decimal("22.00"),
        "accepts_online_consultations": True,
        "available_for_appointments": True,
        "verified": False,
        "verification_note": "Fictional demo data - not a real lawyer",
        "bio": "Demo profile for deceased estates, inheritance and wills.",
    },
]


class Command(BaseCommand):
    help = "Seed fictional civilian-module lawyers for prototype testing."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for data in DUMMY_LAWYERS:
            lawyer, was_created = Lawyer.objects.update_or_create(
                full_name=data["full_name"],
                city=data["city"],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                updated += 1

            LawyerReview.objects.get_or_create(
                lawyer=lawyer,
                reviewer_name="Demo reviewer",
                matter_type=lawyer.practice_areas[0] if lawyer.practice_areas else "general",
                defaults={"rating": 5, "comment": "Fictional review for UI testing only."},
            )

        self.stdout.write(self.style.SUCCESS(f"Seed complete. Created {created}, updated {updated}. Fictional demo data only."))
