from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.auth import get_user_from_request
from .models import (
    Community, Post, Comment, PostLike, SavedPost,
    LawyerProfile, MentorshipProgramme, MentorshipEnrollment, MentorshipMessage,
)
from .serializers import (
    CommunitySerializer, PostListSerializer, PostDetailSerializer, PostCreateSerializer,
    CommentSerializer, LawyerProfileSerializer, MentorshipProgrammeSerializer,
    MentorshipProgrammeDetailSerializer, MentorshipMessageSerializer, FindLawyerRequestSerializer,
)


def api_error(message, http_status=400, **extra):
    return Response({"ok": False, "success": False, "message": message, **extra}, status=http_status)


class CommunityListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"ok": True, "communities": CommunitySerializer(Community.objects.all(), many=True).data})


class PostListCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_user_from_request(request)
        qs = Post.objects.select_related("author", "community").prefetch_related("comments", "likes")
        community_key = request.query_params.get("community")
        if community_key and community_key != "all":
            qs = qs.filter(community__key=community_key)
        # Enforce the visibility rule in Python rather than a giant queryset filter, since
        # Post.visible_to() is the single source of truth for this rule elsewhere too -
        # duplicating the logic as a separate ORM filter here would risk the two drifting
        # apart over time.
        posts = [p for p in qs[:200] if p.visible_to(user)]
        return Response({"ok": True, "posts": PostListSerializer(posts, many=True).data})

    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return api_error("Sign in to post.", 401)
        serializer = PostCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        return Response({"ok": True, "post": PostDetailSerializer(post).data}, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, post_id):
        user = get_user_from_request(request)
        post = get_object_or_404(Post.objects.select_related("author", "community"), id=post_id)
        if not post.visible_to(user):
            return api_error("You don't have access to this post.", 403)
        return Response({"ok": True, "post": PostDetailSerializer(post).data})


class CommentCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, post_id):
        user = get_user_from_request(request)
        if not user:
            return api_error("Sign in to reply.", 401)
        post = get_object_or_404(Post, id=post_id)
        if not post.can_comment(user):
            return api_error("Only lawyers can respond to this question." if post.is_student_only else "You can't comment on this post.", 403)
        text = (request.data.get("text") or "").strip()
        if not text:
            return api_error("Write something before replying.", 400)
        profile = getattr(user, "lafre_profile", None)
        comment = Comment.objects.create(post=post, author=user, author_role=profile.role if profile else "", text=text)
        return Response({"ok": True, "comment": CommentSerializer(comment).data}, status=status.HTTP_201_CREATED)


class PostLikeToggleView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, post_id):
        user = get_user_from_request(request)
        if not user:
            return api_error("Sign in to like a post.", 401)
        post = get_object_or_404(Post, id=post_id)
        like, created = PostLike.objects.get_or_create(post=post, user=user)
        if not created:
            like.delete()
        return Response({"ok": True, "liked": created, "like_count": post.likes.count()})


class PostSaveToggleView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, post_id):
        user = get_user_from_request(request)
        if not user:
            return api_error("Sign in to save a post.", 401)
        post = get_object_or_404(Post, id=post_id)
        saved, created = SavedPost.objects.get_or_create(post=post, user=user)
        if not created:
            saved.delete()
        return Response({"ok": True, "saved": created})


class LawyerListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        qs = LawyerProfile.objects.select_related("user").prefetch_related("badges", "promotions")
        area = request.query_params.get("area")
        if area:
            qs = qs.filter(practice_area__icontains=area)
        lawyers = sorted(qs, key=lambda l: (not l.is_sponsored_now, -float(l.rating)))
        return Response({"ok": True, "lawyers": LawyerProfileSerializer(lawyers, many=True).data})


class LawyerDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, slug):
        lawyer = get_object_or_404(LawyerProfile.objects.select_related("user").prefetch_related("badges"), slug=slug)
        return Response({"ok": True, "lawyer": LawyerProfileSerializer(lawyer).data})


class FindLawyerRequestView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return api_error("Sign in to request a lawyer.", 401)
        serializer = FindLawyerRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        req = serializer.save()
        # Simple match: same practice-area text match, sponsored first, then by rating -
        # a real matching algorithm can replace this later without changing the API shape.
        matches = LawyerProfile.objects.filter(practice_area__icontains=req.category or "") or LawyerProfile.objects.all()
        matches = sorted(matches, key=lambda l: (not l.is_sponsored_now, -float(l.rating)))[:3]
        req.matched_lawyers.set(matches)
        return Response({"ok": True, "request_id": req.id, "lawyers": LawyerProfileSerializer(matches, many=True).data}, status=status.HTTP_201_CREATED)


class MentorshipListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        qs = MentorshipProgramme.objects.select_related("lawyer__user").prefetch_related("enrollments")
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(title__icontains=q)
        return Response({"ok": True, "programmes": MentorshipProgrammeSerializer(qs, many=True).data})


class MentorshipDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, programme_id):
        programme = get_object_or_404(MentorshipProgramme.objects.prefetch_related("materials", "messages", "enrollments"), id=programme_id)
        return Response({"ok": True, "programme": MentorshipProgrammeDetailSerializer(programme).data})


class MentorshipJoinView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, programme_id):
        user = get_user_from_request(request)
        if not user:
            return api_error("Sign in to join a mentorship programme.", 401)
        programme = get_object_or_404(MentorshipProgramme, id=programme_id)
        MentorshipEnrollment.objects.get_or_create(programme=programme, student=user)
        return Response({"ok": True, "programme": MentorshipProgrammeDetailSerializer(programme).data})


class MentorshipMessageCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, programme_id):
        user = get_user_from_request(request)
        if not user:
            return api_error("Sign in to post in this group.", 401)
        programme = get_object_or_404(MentorshipProgramme, id=programme_id)
        is_member = MentorshipEnrollment.objects.filter(programme=programme, student=user).exists() or getattr(programme.lawyer, "user_id", None) == user.id
        if not is_member:
            return api_error("Join this programme before posting in its group.", 403)
        text = (request.data.get("text") or "").strip()
        if not text:
            return api_error("Write something first.", 400)
        message = MentorshipMessage.objects.create(programme=programme, author=user, text=text)
        return Response({"ok": True, "message": MentorshipMessageSerializer(message).data}, status=status.HTTP_201_CREATED)
