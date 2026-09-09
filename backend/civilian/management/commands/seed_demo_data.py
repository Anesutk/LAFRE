from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import UserProfile
from civilian.models import (
    AdminNotification,
    AppointmentRequest,
    CitizenMatter,
    DocumentReviewRequest,
    GeneratedDocument,
    KnowledgeBaseFailure,
    KnowledgeBaseNote,
    Lawyer,
    LawyerAssignment,
    LawyerBadge,
    LegalMatter,
    MatterPayment,
    PathwayDocumentTemplate,
    PlatformSetting,
    PublicAnnouncement,
    PublicMatterType,
    SupportResource,
)
from forum.models import (
    Comment,
    Community,
    FindLawyerRequest,
    LawyerBadge as ForumLawyerBadge,
    LawyerEngagementEvent,
    LawyerProfile as ForumLawyerProfile,
    MentorshipEnrollment,
    MentorshipMaterial,
    MentorshipMessage,
    MentorshipProgramme,
    Post,
    PostLike,
    SavedPost,
)
from students.models import Flashcard, FlashcardDeck, StudentChat, StudentDocument, StudentMessage


DEMO_PASSWORD = "DemoPass!2026"


class Command(BaseCommand):
    help = "Create repeatable fictional demo data for local or staging testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete demo records before recreating them. Only records marked demo are removed.",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["reset"]:
                self.reset_demo_data()
            users = self.seed_users()
            lawyers = self.seed_civilian_lawyers(users)
            self.seed_civilian_content(users, lawyers)
            forum_lawyers = self.seed_forum_data(users)
            self.seed_student_data(users)
            self.stdout.write(self.style.SUCCESS(
                "Demo data ready. Fictional records use demo emails and can be safely reset with --reset."
            ))
            self.stdout.write(f"Demo login password for all seeded accounts: {DEMO_PASSWORD}")
            self.stdout.write(f"Seeded {len(users)} users, {len(lawyers)} civilian lawyers, and {len(forum_lawyers)} forum lawyer profiles.")

    def user(self, email, first_name, last_name, role, status, **extra):
        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = role == "admin"
        user.is_superuser = False
        user.set_password(DEMO_PASSWORD)
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.requested_role = role
        profile.status = status
        profile.email_verified = True
        profile.phone = extra.pop("phone", "")
        profile.city = extra.pop("city", "")
        profile.institution = extra.pop("institution", "")
        profile.organisation = extra.pop("organisation", "")
        profile.practice_area = extra.pop("practice_area", "")
        profile.access_reason = extra.pop("access_reason", "Demo account for staging and interface testing.")
        profile.can_use_civilian = role in {"citizen", "lawyer"}
        profile.can_use_student = role == "student"
        profile.can_generate_documents = role == "citizen"
        profile.can_submit_review = role == "lawyer"
        profile.can_request_lawyer = role == "citizen"
        profile.can_access_lawyer_portal = role == "lawyer"
        profile.can_access_admin = role == "admin"
        profile.can_upload_assignments = role == "student"
        profile.can_use_assignment_help = role == "student"
        profile.daily_message_limit = 30 if role == "student" else 0
        profile.monthly_message_limit = 600 if role == "student" else 0
        profile.daily_document_limit = 10 if role in {"student", "citizen"} else 0
        profile.monthly_document_limit = 100 if role in {"student", "citizen"} else 0
        profile.daily_upload_limit = 10 if role in {"student", "citizen", "lawyer"} else 0
        profile.monthly_upload_limit = 100 if role in {"student", "citizen", "lawyer"} else 0
        for key, value in extra.items():
            setattr(profile, key, value)
        profile.save()
        return user

    def seed_users(self):
        return {
            "admin": self.user("demo.admin@example.test", "Amara", "Admin", "admin", "approved"),
            "citizen": self.user(
                "demo.citizen@example.test", "Tendai", "Moyo", "citizen", "approved",
                city="Harare", phone="+263 77 100 2001",
            ),
            "student": self.user(
                "demo.student@example.test", "Rudo", "Ncube", "student", "approved",
                city="Bulawayo", institution="University of Zimbabwe", phone="+263 77 100 2002",
            ),
            "pending": self.user(
                "demo.pending@example.test", "Kuda", "Dube", "citizen", "pending",
                city="Gweru", access_reason="Requesting help with a tenancy dispute.",
            ),
            "lawyer_one": self.user(
                "demo.lawyer.one@example.test", "Nyasha", "Moyo", "lawyer", "approved",
                city="Harare", phone="+263 77 100 2101", practice_area="Property and commercial law",
            ),
            "lawyer_two": self.user(
                "demo.lawyer.two@example.test", "Farai", "Ndlovu", "lawyer", "approved",
                city="Bulawayo", phone="+263 77 100 2102", practice_area="Family and employment law",
            ),
        }

    def seed_civilian_lawyers(self, users):
        records = [
            ("lawyer_one", "Nyasha Moyo", "Moyo Legal Practice", "nyasha-moyo", ["property", "contracts"], ["Lease review", "Property transfer guidance", "Demand letters"], ["English", "Shona"], "Harare", "Harare", "4.80"),
            ("lawyer_two", "Farai Ndlovu", "Ndlovu Family Law Chambers", "farai-ndlovu", ["family", "employment"], ["Maintenance guidance", "Employment contracts", "Mediation preparation"], ["English", "Ndebele"], "Bulawayo", "Bulawayo", "4.60"),
        ]
        lawyers = []
        for key, name, firm, slug, areas, services, languages, city, province, rating in records:
            lawyer, _ = Lawyer.objects.update_or_create(
                slug=f"demo-{slug}",
                defaults={
                    "user": users[key], "full_name": name, "firm_name": firm,
                    "practice_areas": areas, "services": services, "languages": languages,
                    "city": city, "province": province, "address": f"Demo office, {city} CBD",
                    "email": users[key].email, "phone": users[key].lafre_profile.phone,
                    "website": "https://example.test/demo-lawyer", "years_experience": 8,
                    "consultation_mode": Lawyer.ConsultationMode.BOTH,
                    "consultation_fee_usd": Decimal("25.00"), "accepts_free_legal_aid": True,
                    "available_for_appointments": True, "verified": True,
                    "verification_note": "Fictional demo profile for testing only.",
                    "bio": f"Fictional demo lawyer focusing on {', '.join(areas)} matters.", "is_active": True,
                },
            )
            lawyers.append(lawyer)
        for name, description in [
            ("Demo Verified", "Fictional verification badge for staging."),
            ("Demo Legal Aid", "Fictional legal-aid availability badge."),
        ]:
            badge, _ = LawyerBadge.objects.get_or_create(name=name, defaults={"description": description})
            for lawyer in lawyers:
                lawyer.badges.add(badge)
        return lawyers

    def seed_civilian_content(self, users, lawyers):
        template, _ = PathwayDocumentTemplate.objects.update_or_create(
            title="Demo Lending Agreement Template",
            defaults={
                "matter_type": "lending_money", "document_type": "loan_agreement",
                "description": "Fictional template for testing document generation and review.",
                "support_note": "Demo content only. Obtain professional advice before relying on any document.",
                "requires_practitioner_review": True, "requires_certification_or_stamp": False,
                "active": True, "sort_order": 1, "version": 1, "last_reviewed_by": "Demo legal content team",
            },
        )
        note, _ = KnowledgeBaseNote.objects.update_or_create(
            title="Demo: lending agreement safety checks",
            defaults={
                "body": "Confirm the parties, amount, repayment dates, signatures, proof of payment, and any security before relying on a lending agreement.",
                "tags": ["demo", "lending", "agreements"], "matter_type": "lending_money", "topic": "document review",
                "verified": True, "visible_to_citizen": True, "active": True,
            },
        )
        PublicMatterType.objects.update_or_create(
            key="demo-tenancy-dispute",
            defaults={
                "letter": "T", "group": "Housing", "title": "Tenancy dispute",
                "short_description": "Explore a fictional rental disagreement pathway.",
                "detailed_description": "Demo pathway covering rent, repairs, notices, and communication records.",
                "kb_terms": ["rent", "notice", "repairs"], "intake_questions": [{"key": "issue", "label": "What happened?"}],
                "urgency_keywords": ["eviction", "unsafe"], "requires_location": True, "active": True, "sort_order": 1,
            },
        )
        PublicAnnouncement.objects.update_or_create(
            title="Demo legal support notice",
            defaults={
                "body": "This is fictional staging content used to test public announcements.",
                "cta_label": "View resources", "cta_url": "/legal-help", "active": True, "collapsible": True,
                "priority": "normal", "sort_order": 1,
            },
        )
        SupportResource.objects.update_or_create(
            name="Demo Community Legal Clinic",
            defaults={
                "resource_type": "legal_aid", "city": "Harare", "province": "Harare",
                "address": "Demo Civic Centre, Harare", "phone": "+263 77 100 2999", "email": "clinic@example.test",
                "notes": "Fictional resource for directory and filtering tests.", "keywords": ["legal aid", "housing", "family"],
                "verified": True, "active": True, "source_note": "Fictional demo data.",
            },
        )
        PlatformSetting.objects.update_or_create(
            key="demo-contact-email", defaults={"label": "Demo contact email", "value": "support@example.test", "is_public": True}
        )
        matter, _ = LegalMatter.objects.update_or_create(
            title="Demo family loan repayment matter",
            defaults={
                "user": users["citizen"], "pathway_id": "demo-lending-money", "issue_type": "lending_money",
                "city": "Harare", "description": "A fictional loan repayment matter for admin queue testing.",
                "support_route": "lawyer_review", "urgency": "normal", "answers_json": {"amount": "1200", "currency": "USD"},
                "guidance_json": {"next_step": "Collect the agreement and payment records."}, "source_count": 2,
                "grounding_status": "verified", "status": "review_requested", "admin_notes": "Demo matter for staging.",
            },
        )
        document, _ = GeneratedDocument.objects.update_or_create(
            title="Demo loan agreement document",
            defaults={
                "user": users["citizen"], "matter": matter, "document_type": "loan_agreement",
                "content": "DEMO DOCUMENT\nThis fictional agreement is for interface testing only.",
                "template_source_note": "Demo Lending Agreement Template", "status": "ready",
                "metadata": {"demo": True, "version": 1},
            },
        )
        citizen_matter, _ = CitizenMatter.objects.update_or_create(
            title="Demo citizen lending matter",
            defaults={
                "user": users["citizen"], "matter_type": "lending_money",
                "status": CitizenMatter.Status.REVIEW_REQUESTED,
                "intake_json": {"amount": "1200", "currency": "USD", "demo": True},
                "validation_json": {"valid": True, "demo": True},
                "kb_support_json": {"source_count": 2, "demo": True},
                "smart_summary_json": {"summary": "Fictional lending matter for admin testing."},
                "document_template": template,
                "generated_document_text": "DEMO DOCUMENT\nThis fictional agreement is for interface testing only.",
            },
        )
        review, _ = DocumentReviewRequest.objects.update_or_create(
            document=document,
            defaults={
                "user": users["citizen"], "assigned_lawyer": lawyers[0],
                "review_type": "review_only", "status": DocumentReviewRequest.Status.ASSIGNED,
                "user_note": "Please check the repayment dates and signature section.",
                "admin_note": "Demo request assigned for queue testing.",
            },
        )
        LawyerAssignment.objects.update_or_create(
            document_review=review,
            defaults={"lawyer": lawyers[0], "matter": matter, "assigned_by": users["admin"], "status": "assigned", "notes": "Demo assignment."},
        )
        MatterPayment.objects.update_or_create(
            matter=citizen_matter, amount=Decimal("1200.00"), defaults={"due_date": timezone.localdate() + timedelta(days=30), "currency": "USD", "status": "pending", "notes": "Demo payment schedule."}
        )
        AppointmentRequest.objects.update_or_create(
            matter=matter,
            defaults={"user": users["citizen"], "lawyer": lawyers[0], "request_note": "Demo request for a consultation about the agreement.", "proposed_time": timezone.now() + timedelta(days=3), "status": "requested", "communication_options": ["email", "video"]},
        )
        KnowledgeBaseFailure.objects.update_or_create(
            search_query="demo tenancy repairs", defaults={"user": users["student"], "user_issue": "Demo unresolved knowledge lookup.", "knowledge_base_id": "demo-kb", "region": "Harare", "source_count": 0, "action_needed": "Review demo source coverage.", "resolved": False, "admin_notes": "Fictional alert for admin testing."}
        )
        AdminNotification.objects.update_or_create(
            title="Demo review request received", defaults={"message": "A fictional citizen submitted a document review request.", "type": "review_request", "priority": "high", "related_user": users["citizen"], "related_object_type": "document_review", "related_object_id": review.id, "metadata": {"demo": True}, "is_read": False}
        )

    def seed_forum_data(self, users):
        communities = []
        for key, name, color, description, order in [
            ("demo-housing", "Housing and Tenancy", "#2d6a6a", "Fictional housing and rental discussions.", 1),
            ("demo-work", "Work and Employment", "#b36a3c", "Fictional workplace rights discussions.", 2),
            ("demo-study", "Law Student Study", "#4d648d", "Fictional study and mentorship discussions.", 3),
        ]:
            community, _ = Community.objects.update_or_create(key=key, defaults={"name": name, "color": color, "description": description, "order": order})
            communities.append(community)
        profiles = []
        for key, slug, firm, area, location, phone, email, bio in [
            ("lawyer_one", "demo-nyasha-moyo", "Moyo Legal Practice", "Property and contracts", "Harare", "+263 77 100 2101", "demo.lawyer.one@example.test", "Fictional profile for property and contract mentoring."),
            ("lawyer_two", "demo-farai-ndlovu", "Ndlovu Family Law Chambers", "Family and employment", "Bulawayo", "+263 77 100 2102", "demo.lawyer.two@example.test", "Fictional profile for family and employment mentoring."),
        ]:
            profile, _ = ForumLawyerProfile.objects.update_or_create(
                slug=slug,
                defaults={"user": users[key], "firm_name": firm, "practice_area": area, "location": location, "years_experience": 8, "bio": bio, "phone": phone, "public_email": email, "verified": True, "mentorship_available": True},
            )
            profiles.append(profile)
        for name, icon, color in [("Demo Verified", "V", "#2d6a6a"), ("Demo Mentor", "M", "#b36a3c")]:
            badge, _ = ForumLawyerBadge.objects.update_or_create(name=name, defaults={"icon": icon, "color": color})
            for profile in profiles:
                profile.badges.add(badge)
        posts = []
        post_data = [
            ("demo-housing", users["citizen"], Post.AuthorRole.CIVILIAN, "Demo: deposit and repair question", "This fictional post tests a civilian housing question and lawyer responses."),
            ("demo-study", users["student"], Post.AuthorRole.STUDENT, "Demo: preparing for a moot court", "This fictional student post tests lawyer-only visibility and commenting."),
        ]
        for community_key, author, role, title, text in post_data:
            post, _ = Post.objects.update_or_create(title=title, author=author, defaults={"community": next(c for c in communities if c.key == community_key), "author_role": role, "text": text, "language": "en"})
            posts.append(post)
        Comment.objects.update_or_create(post=posts[0], author=users["lawyer_one"], defaults={"author_role": "lawyer", "text": "This fictional answer explains what records a tenant should keep."})
        Comment.objects.update_or_create(post=posts[1], author=users["lawyer_two"], defaults={"author_role": "lawyer", "text": "This fictional answer suggests a structured preparation plan."})
        for post in posts:
            PostLike.objects.get_or_create(post=post, user=users["student"])
            SavedPost.objects.get_or_create(post=post, user=users["citizen"])
        for profile, post in zip(profiles, posts):
            LawyerEngagementEvent.objects.get_or_create(lawyer=profile, event_type="profile_view", related_post=post, defaults={"points": Decimal("4.50")})
            profile.recalculate_rating()
        programme, _ = MentorshipProgramme.objects.update_or_create(
            title="Demo foundations of legal practice",
            defaults={"lawyer": profiles[0], "area": "Legal research and client communication", "description": "Fictional mentorship programme for testing enrollment and messaging.", "topics": ["Client interviews", "Research notes", "Professional writing"], "weeks": 6, "is_free": True},
        )
        MentorshipEnrollment.objects.get_or_create(programme=programme, student=users["student"])
        MentorshipMessage.objects.update_or_create(programme=programme, author=users["student"], defaults={"text": "This fictional message tests the mentorship conversation."})
        MentorshipMaterial.objects.update_or_create(programme=programme, title="Demo research checklist", defaults={"file_url": "https://example.test/demo-research-checklist", "material_type": "Link"})
        request, _ = FindLawyerRequest.objects.update_or_create(citizen=users["citizen"], category="Property", defaults={"description": "Fictional request for help with a lease review.", "location_text": "Harare"})
        request.matched_lawyers.set(profiles)
        return profiles

    def seed_student_data(self, users):
        chat, _ = StudentChat.objects.update_or_create(
            user=users["student"], title="Demo constitutional law study chat",
            defaults={"summary": "Fictional chat for testing history, messages, and flashcards.", "session_id": "demo-student-session"},
        )
        StudentMessage.objects.update_or_create(chat=chat, role=StudentMessage.Role.USER, text="Explain the difference between a statute and a regulation.", defaults={"response_payload": {"demo": True}})
        StudentMessage.objects.update_or_create(chat=chat, role=StudentMessage.Role.ASSISTANT, text="A statute is enacted by the legislature; a regulation is made under delegated authority.", defaults={"response_payload": {"demo": True, "source_count": 2}})
        StudentDocument.objects.update_or_create(user=users["student"], title="Demo constitutional law notes", defaults={"extracted_text": "Fictional notes covering constitutional interpretation and delegated legislation.", "source_type": "demo_seed", "safe_metadata": {"demo": True, "pages": 3}, "active": True})
        deck, _ = FlashcardDeck.objects.update_or_create(user=users["student"], title="Demo public law flashcards", defaults={"source_chat": chat})
        cards = [
            ("What is judicial review?", "The process by which courts examine the legality of public decisions.", "Administrative law", "medium"),
            ("What is delegated legislation?", "Rules made by an authorised body under powers granted by an Act.", "Constitutional law", "easy"),
            ("What makes a precedent binding?", "The applicable holding of a higher court in the relevant hierarchy.", "Legal method", "hard"),
        ]
        for front, back, topic, difficulty in cards:
            Flashcard.objects.update_or_create(deck=deck, front=front, defaults={"back": back, "topic": topic, "difficulty": difficulty, "source_label": "Demo seed"})

    def reset_demo_data(self):
        User.objects.filter(username__startswith="demo.").delete()
        # User deletion cascades user-owned demo records. These records use stable demo prefixes
        # and are cleaned separately because several older models keep nullable user links.
        for model, field in [
            (PlatformSetting, "key"), (PublicAnnouncement, "title"), (PublicMatterType, "key"),
            (SupportResource, "name"), (PathwayDocumentTemplate, "title"), (KnowledgeBaseNote, "title"),
            (Community, "key"), (Post, "title"), (ForumLawyerBadge, "name"),
            (MentorshipProgramme, "title"), (StudentChat, "title"), (FlashcardDeck, "title"),
        ]:
            model.objects.filter(**{f"{field}__startswith": "demo"}).delete()
        Lawyer.objects.filter(slug__startswith="demo-").delete()
        ForumLawyerProfile.objects.filter(slug__startswith="demo-").delete()
        LegalMatter.objects.filter(title__startswith="Demo").delete()
        CitizenMatter.objects.filter(title__startswith="Demo").delete()
        GeneratedDocument.objects.filter(title__startswith="Demo").delete()
        LawyerBadge.objects.filter(name__startswith="Demo").delete()
        KnowledgeBaseFailure.objects.filter(search_query__startswith="demo").delete()
        AdminNotification.objects.filter(title__startswith="Demo").delete()
