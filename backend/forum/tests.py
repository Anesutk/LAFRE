from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from .models import Community, Post, PostLike, SavedPost, Comment


class StudentForumFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student@example.com", email="student@example.com", password="StudentPass1!",
            first_name="Forum", last_name="Student",
        )
        UserProfile.objects.create(
            user=self.student, role=UserProfile.Role.STUDENT, requested_role=UserProfile.Role.STUDENT,
            status=UserProfile.Status.APPROVED, can_use_student=True,
        )
        self.lawyer = User.objects.create_user(
            username="lawyer@example.com", email="lawyer@example.com", password="LawyerPass1!",
            first_name="Forum", last_name="Lawyer",
        )
        UserProfile.objects.create(
            user=self.lawyer, role=UserProfile.Role.LAWYER, requested_role=UserProfile.Role.LAWYER,
            status=UserProfile.Status.APPROVED, can_access_lawyer_portal=True,
        )
        self.citizen = User.objects.create_user(
            username="citizen@example.com", email="citizen@example.com", password="CitizenPass1!",
            first_name="Forum", last_name="Citizen",
        )
        UserProfile.objects.create(
            user=self.citizen, role=UserProfile.Role.CITIZEN, requested_role=UserProfile.Role.CITIZEN,
            status=UserProfile.Status.APPROVED, can_use_civilian=True,
        )
        self.community = Community.objects.create(key="study", name="Study Questions")
        self.client = APIClient()

    def login(self, email, password):
        response = self.client.post("/api/accounts/login/", {"email": email, "password": password}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['token']}")
        return response

    def test_student_login_redirects_to_forum_and_can_create_post(self):
        self.login("student@example.com", "StudentPass1!")
        response = self.client.post(
            "/api/forum/posts/",
            {"title": "How should I approach this case?", "text": "I am comparing two authorities for a study group.", "community": self.community.id},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["post"]["author_name"], "Forum Student")
        self.assertTrue(response.data["post"]["liked"] is False)
        post = Post.objects.get()
        self.assertEqual(post.author, self.student)

    def test_student_can_like_and_save_civilian_post_and_persistence_is_real(self):
        post = Post.objects.create(author=self.citizen, author_role="civilian", community=self.community, title="Citizen question", text="What is the general position?")
        self.login("student@example.com", "StudentPass1!")
        like = self.client.post(f"/api/forum/posts/{post.id}/like/", {}, format="json")
        self.assertEqual(like.status_code, 200)
        self.assertTrue(like.data["liked"])
        save = self.client.post(f"/api/forum/posts/{post.id}/save/", {}, format="json")
        self.assertEqual(save.status_code, 200)
        self.assertTrue(save.data["saved"])
        detail = self.client.get(f"/api/forum/posts/{post.id}/")
        self.assertTrue(detail.data["post"]["liked"])
        self.assertTrue(detail.data["post"]["saved"])
        self.assertEqual(PostLike.objects.count(), 1)
        self.assertEqual(SavedPost.objects.count(), 1)

    def test_student_can_reply_to_civilian_post(self):
        post = Post.objects.create(author=self.citizen, author_role="civilian", community=self.community, title="Citizen question", text="Please explain this.")
        self.login("student@example.com", "StudentPass1!")
        response = self.client.post(f"/api/forum/posts/{post.id}/comments/", {"text": "Here is how I understand the issue."}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.count(), 1)

    def test_student_post_is_not_visible_to_other_students_and_only_lawyers_may_reply(self):
        post = Post.objects.create(author=self.student, author_role="student", community=self.community, title="Private student question", text="Only the author and lawyers should see this.")
        self.login("citizen@example.com", "CitizenPass1!")
        self.assertEqual(self.client.get(f"/api/forum/posts/{post.id}/").status_code, 403)
        self.login("student@example.com", "StudentPass1!")
        self.assertEqual(self.client.get(f"/api/forum/posts/{post.id}/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/forum/posts/{post.id}/comments/", {"text": "I cannot answer my own lawyer-only question."}, format="json").status_code, 403)
        self.login("lawyer@example.com", "LawyerPass1!")
        response = self.client.post(f"/api/forum/posts/{post.id}/comments/", {"text": "A verified lawyer can respond here."}, format="json")
        self.assertEqual(response.status_code, 201)
