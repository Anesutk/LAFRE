from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from .models import Community, Post


class StudentForumFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="StudentPass1!",
            first_name="Forum",
            last_name="Student",
        )
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.STUDENT,
            requested_role=UserProfile.Role.STUDENT,
            status=UserProfile.Status.APPROVED,
            can_use_student=True,
        )
        self.community = Community.objects.create(key="study", name="Study Questions")
        self.client = APIClient()

    def test_student_login_redirects_to_forum_and_can_create_post(self):
        login = self.client.post(
            "/api/accounts/login/",
            {"email": "student@example.com", "password": "StudentPass1!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["redirect_to"], "/forum")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['token']}")
        response = self.client.post(
            "/api/forum/posts/",
            {
                "title": "How should I approach this case?",
                "text": "I am comparing two authorities for a study group.",
                "community": self.community.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["post"]["author_name"], "Forum Student")
        self.assertEqual(Post.objects.get().author, self.user)
