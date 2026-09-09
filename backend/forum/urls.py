from django.urls import path

from . import views

urlpatterns = [
    path("communities/", views.CommunityListView.as_view(), name="forum-communities"),

    path("posts/", views.PostListCreateView.as_view(), name="forum-posts"),
    path("posts/<int:post_id>/", views.PostDetailView.as_view(), name="forum-post-detail"),
    path("posts/<int:post_id>/comments/", views.CommentCreateView.as_view(), name="forum-post-comments"),
    path("posts/<int:post_id>/like/", views.PostLikeToggleView.as_view(), name="forum-post-like"),
    path("posts/<int:post_id>/save/", views.PostSaveToggleView.as_view(), name="forum-post-save"),

    path("lawyers/", views.LawyerListView.as_view(), name="forum-lawyers"),
    path("lawyers/<slug:slug>/", views.LawyerDetailView.as_view(), name="forum-lawyer-detail"),
    path("find-a-lawyer/", views.FindLawyerRequestView.as_view(), name="forum-find-a-lawyer"),

    path("mentorship/", views.MentorshipListView.as_view(), name="forum-mentorship"),
    path("mentorship/<int:programme_id>/", views.MentorshipDetailView.as_view(), name="forum-mentorship-detail"),
    path("mentorship/<int:programme_id>/join/", views.MentorshipJoinView.as_view(), name="forum-mentorship-join"),
    path("mentorship/<int:programme_id>/messages/", views.MentorshipMessageCreateView.as_view(), name="forum-mentorship-messages"),
]
