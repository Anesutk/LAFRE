from rest_framework import serializers

from accounts.auth import get_user_from_request

from .models import (
    Community, Post, Comment, LawyerProfile, LawyerBadge,
    MentorshipProgramme, MentorshipMessage, MentorshipMaterial, FindLawyerRequest,
)


class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = ["id", "key", "name", "color", "description"]


def _author_name(user):
    if not user:
        return "LAFRE"
    return user.get_full_name() or user.email


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "post", "author_name", "author_role", "is_ai_generated", "text", "created_at"]
        read_only_fields = ["is_ai_generated"]

    def get_author_name(self, obj):
        return "LAFRE" if obj.is_ai_generated else _author_name(obj.author)


class PostListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    community_detail = CommunitySerializer(source="community", read_only=True)
    reply_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    saved = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "title", "text", "author_name", "author_role", "community_detail", "language", "created_at", "reply_count", "like_count", "liked", "saved"]

    def get_author_name(self, obj):
        return _author_name(obj.author)

    def get_reply_count(self, obj):
        return obj.comments.count()

    def get_like_count(self, obj):
        return obj.likes.count()

    def _request_user(self):
        request = self.context.get("request") if hasattr(self, "context") else None
        user = getattr(request, "user", None) if request else None
        # api views use a manual token rather than DRF authentication, so request.user
        # may be AnonymousUser. Resolve the same token used by the platform.
        if request:
            try:
                return get_user_from_request(request)
            except Exception:
                return None
        return user if getattr(user, "is_authenticated", False) else None

    def get_liked(self, obj):
        user = self._request_user()
        return bool(user and user.is_authenticated and obj.likes.filter(user=user).exists())

    def get_saved(self, obj):
        user = self._request_user()
        return bool(user and user.is_authenticated and obj.saved_by.filter(user=user).exists())


class PostDetailSerializer(PostListSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ["comments"]


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "title", "text", "community", "language"]

    def create(self, validated_data):
        request = self.context["request"]
        user = get_user_from_request(request)
        profile = getattr(user, "lafre_profile", None)
        role = profile.role if profile and profile.role in ("student", "lawyer") else "civilian"
        return Post.objects.create(author=user, author_role=role, **validated_data)


class LawyerBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerBadge
        fields = ["id", "name", "icon", "color"]


class LawyerProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    badges = LawyerBadgeSerializer(many=True, read_only=True)
    sponsored = serializers.BooleanField(source="is_sponsored_now", read_only=True)
    featured = serializers.BooleanField(source="is_featured_now", read_only=True)

    class Meta:
        model = LawyerProfile
        fields = [
            "id", "slug", "name", "firm_name", "practice_area", "location", "years_experience",
            "bio", "phone", "public_email", "verified", "mentorship_available", "badges",
            "rating", "reviews_count", "sponsored", "featured",
        ]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.email


class MentorshipMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorshipMaterial
        fields = ["id", "title", "file_url", "material_type"]


class MentorshipMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = MentorshipMessage
        fields = ["id", "author_name", "text", "created_at"]

    def get_author_name(self, obj):
        return _author_name(obj.author)


class MentorshipProgrammeSerializer(serializers.ModelSerializer):
    lawyer_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    joined = serializers.SerializerMethodField()
    is_mentor = serializers.SerializerMethodField()

    class Meta:
        model = MentorshipProgramme
        fields = ["id", "title", "area", "description", "topics", "weeks", "is_free", "fee_amount", "lawyer_name", "student_count", "joined", "is_mentor"]

    def get_lawyer_name(self, obj):
        return obj.lawyer.user.get_full_name() or obj.lawyer.user.email

    def get_student_count(self, obj):
        return obj.enrollments.count()

    def _request_user(self):
        request = self.context.get("request") if hasattr(self, "context") else None
        if not request:
            return None
        try:
            return get_user_from_request(request)
        except Exception:
            return None

    def get_joined(self, obj):
        user = self._request_user()
        return bool(user and obj.enrollments.filter(student=user).exists())

    def get_is_mentor(self, obj):
        user = self._request_user()
        return bool(user and obj.lawyer.user_id == user.id)


class MentorshipProgrammeDetailSerializer(MentorshipProgrammeSerializer):
    materials = MentorshipMaterialSerializer(many=True, read_only=True)
    messages = serializers.SerializerMethodField()

    def get_messages(self, obj):
        user = self._request_user()
        if not user:
            return []
        is_member = obj.enrollments.filter(student=user).exists() or obj.lawyer.user_id == user.id
        if not is_member:
            return []
        return MentorshipMessageSerializer(obj.messages.all(), many=True).data

    class Meta(MentorshipProgrammeSerializer.Meta):
        fields = MentorshipProgrammeSerializer.Meta.fields + ["materials", "messages"]


class FindLawyerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindLawyerRequest
        fields = ["id", "category", "description", "location_text", "created_at"]

    def create(self, validated_data):
        return FindLawyerRequest.objects.create(citizen=self.context["request"].user, **validated_data)
