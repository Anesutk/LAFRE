"""
Models for the LAFRE forum / lawyer marketplace / mentorship platform.

Design note: rather than reworking civilian.Lawyer/CitizenMatter (the older, partially-built
models from before this platform vision existed), this is a fresh, self-contained app. The
older civilian models are left untouched - nothing here deletes or depends on them, so no
data loss risk. If you want them merged/retired later, that's a separate, deliberate step.

Visibility rule (the platform's most important rule, per the product doc):
- A STUDENT-authored post is visible only to lawyers (and the student who wrote it).
- A CIVILIAN-authored post is visible to civilians, students, and lawyers.
- Only a lawyer may answer a student's post. Students and lawyers may both answer a
  civilian's post.
This is enforced in Post.visible_to() below - a single method every view should call through,
so the rule lives in one place instead of being re-implemented per view.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Forum: communities, posts, comments, likes
# ---------------------------------------------------------------------------

class Community(models.Model):
    """A named discussion community (e.g. "Workplace & Employment"). Data-driven rather than
    a hardcoded choices list, so new communities can be added from the admin without a
    migration or a frontend deploy.
    """
    key = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=7, default="#8a887f", help_text="Hex color, e.g. #f97316")
    description = models.CharField(max_length=280, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "communities"

    def __str__(self):
        return self.name


class Post(models.Model):
    class AuthorRole(models.TextChoices):
        CIVILIAN = "civilian", "Civilian"
        STUDENT = "student", "Law student"
        LAWYER = "lawyer", "Lawyer"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts")
    author_role = models.CharField(max_length=20, choices=AuthorRole.choices)
    community = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    title = models.CharField(max_length=220)
    text = models.TextField()
    language = models.CharField(max_length=20, default="en", help_text="Best-effort detected language code, e.g. 'en', 'sn' (Shona)")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title[:60]

    @property
    def is_student_only(self) -> bool:
        """A student's own post is only visible to lawyers (and the student themself) -
        this is the platform's headline permission rule, kept as one property so every
        view/serializer checks the same thing instead of re-deriving it."""
        return self.author_role == self.AuthorRole.STUDENT

    def visible_to(self, user) -> bool:
        if not user or not user.is_authenticated:
            return not self.is_student_only  # guests can browse civilian-authored posts only
        profile = getattr(user, "lafre_profile", None)
        if user.is_superuser or user.is_staff:
            return True
        if self.author_id == user.id:
            return True
        if not profile:
            return not self.is_student_only
        if self.is_student_only:
            return profile.role == "lawyer"
        return True  # civilian-authored posts: visible to civilians, students, and lawyers

    def can_comment(self, user) -> bool:
        """Only a lawyer may answer a student's post; civilian posts can be answered by
        both students and lawyers."""
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "lafre_profile", None)
        if user.is_superuser:
            return True
        if not profile:
            return False
        if self.is_student_only:
            return profile.role == "lawyer"
        return profile.role in ("student", "lawyer")


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_comments", null=True, blank=True)
    author_role = models.CharField(max_length=20, blank=True)
    text = models.TextField()
    # An AI-generated first response is stored as a real Comment (is_ai_generated=True,
    # author=None) so it renders in the normal comment list rather than needing special
    # handling everywhere it's displayed - per the product doc, it should look like an
    # ordinary comment from a "LAFRE" account, not a bot-badged system message.
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.post_id} by {self.author_id or 'LAFRE AI'}"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_likes")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("post", "user")


class SavedPost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saved_by")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_saved_posts")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("post", "user")


# ---------------------------------------------------------------------------
# Lawyer marketplace: profile, badges, promotions, engagement/rating, requests
# ---------------------------------------------------------------------------

class LawyerBadge(models.Model):
    """Admin-assignable badges (e.g. "Verified", "Top Rated", "Rising Star"). Kept as a
    model rather than a fixed choices list so new badge types don't need a migration."""
    name = models.CharField(max_length=60, unique=True)
    icon = models.CharField(max_length=10, default="★", help_text="Emoji or short glyph shown next to the badge")
    color = models.CharField(max_length=7, default="#d99a2b")

    def __str__(self):
        return self.name


class LawyerProfile(models.Model):
    """Lawyers are added by an admin, never self-registered (per the product doc) - the
    linked User account is still created the normal way (so the lawyer can log in), but the
    account + profile pairing happens through the admin, not a public /register flow."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_lawyer_profile")
    slug = models.SlugField(max_length=80, unique=True)
    firm_name = models.CharField(max_length=180, blank=True)
    practice_area = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    public_email = models.EmailField(blank=True)
    verified = models.BooleanField(default=False, help_text="Only verified lawyers show the ★★★ badge anywhere in the app")
    mentorship_available = models.BooleanField(default=False)
    badges = models.ManyToManyField(LawyerBadge, blank=True, related_name="lawyers")
    # rating/reviews_count are cached fields, recalculated from LawyerEngagementEvent by
    # recalculate_rating() below - not hand-edited directly in normal operation.
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-rating"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} ({self.practice_area})"

    @property
    def is_sponsored_now(self) -> bool:
        return self.promotions.filter(tier=LawyerPromotion.Tier.SPONSORED, active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now()).exists()

    @property
    def is_featured_now(self) -> bool:
        return self.promotions.filter(tier=LawyerPromotion.Tier.FEATURED, active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now()).exists()

    def recalculate_rating(self):
        """Placeholder scoring algorithm: rating is a simple weighted average of engagement
        event points, capped at 5.0. This is intentionally simple for the prototype stage -
        the product doc describes a more nuanced "engagement earns rating" system, which
        should replace this function's internals once the real scoring rules are decided,
        without needing to change any caller of this method.
        """
        events = self.engagement_events.all()
        count = events.count()
        if not count:
            self.rating = 0
            self.reviews_count = 0
        else:
            avg_points = sum(e.points for e in events) / count
            self.rating = min(round(avg_points, 2), 5.0)
            self.reviews_count = count
        self.save(update_fields=["rating", "reviews_count"])


class LawyerPromotion(models.Model):
    """Admin-managed lawyer promotion slots ("sponsored" or "featured"), time-bounded so a
    promotion naturally expires rather than needing to be manually turned off."""
    class Tier(models.TextChoices):
        SPONSORED = "sponsored", "Sponsored"
        FEATURED = "featured", "Featured"

    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name="promotions")
    tier = models.CharField(max_length=20, choices=Tier.choices)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.lawyer} — {self.get_tier_display()}"


class LawyerEngagementEvent(models.Model):
    """A raw log of things that should influence a lawyer's rating - answering a question,
    a civilian marking a response helpful, etc. recalculate_rating() reads this log rather
    than a hand-set number, so rating reflects real activity instead of being arbitrarily
    assigned."""
    class EventType(models.TextChoices):
        FORUM_REPLY = "forum_reply", "Replied to a forum post"
        HELPFUL_MARK = "helpful_mark", "Marked helpful by a user"
        PROFILE_VIEW = "profile_view", "Profile viewed"
        MENTORSHIP_SESSION = "mentorship_session", "Ran a mentorship session"

    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name="engagement_events")
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    points = models.DecimalField(max_digits=3, decimal_places=2, default=4.5, help_text="Contribution to the rolling rating average for this event")
    related_post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class FindLawyerRequest(models.Model):
    """Captures a submission from the civilian "Find a Lawyer" flow - category, free-text
    description, and best-effort location - so admins/lawyers can see real demand even
    before any messaging/contact system exists."""
    citizen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lawyer_requests")
    category = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    location_text = models.CharField(max_length=180, blank=True)
    matched_lawyers = models.ManyToManyField(LawyerProfile, blank=True, related_name="matched_requests")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Request from {self.citizen} — {self.category or 'General'}"


# ---------------------------------------------------------------------------
# Mentorship programmes (student <-> lawyer)
# ---------------------------------------------------------------------------

class MentorshipProgramme(models.Model):
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name="mentorship_programmes")
    title = models.CharField(max_length=160)
    area = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    topics = models.JSONField(default=list, blank=True, help_text="List of short strings describing what students will learn")
    weeks = models.PositiveSmallIntegerField(default=4)
    is_free = models.BooleanField(default=True)
    fee_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class MentorshipEnrollment(models.Model):
    programme = models.ForeignKey(MentorshipProgramme, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentorship_enrollments")
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("programme", "student")


class MentorshipMessage(models.Model):
    programme = models.ForeignKey(MentorshipProgramme, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentorship_messages")
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]


class MentorshipMaterial(models.Model):
    programme = models.ForeignKey(MentorshipProgramme, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    file_url = models.URLField(blank=True)
    material_type = models.CharField(max_length=20, default="Link", help_text="e.g. PDF, DOCX, Link")
    created_at = models.DateTimeField(default=timezone.now)
