from django.contrib import admin

from .models import (
    Community, Post, Comment, PostLike, SavedPost,
    LawyerBadge, LawyerProfile, LawyerPromotion, LawyerEngagementEvent, FindLawyerRequest,
    MentorshipProgramme, MentorshipEnrollment, MentorshipMessage, MentorshipMaterial,
)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "color", "order")
    search_fields = ("name", "key")


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "is_ai_generated", "text", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "author_role", "community", "created_at")
    list_filter = ("author_role", "community", "language")
    search_fields = ("title", "text", "author__email", "author__username")
    inlines = [CommentInline]
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "is_ai_generated", "created_at")
    list_filter = ("is_ai_generated",)
    search_fields = ("text", "author__email")


admin.site.register(PostLike)
admin.site.register(SavedPost)


@admin.register(LawyerBadge)
class LawyerBadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "color")


class LawyerPromotionInline(admin.TabularInline):
    """Lets an admin promote a lawyer (sponsored/featured) directly from the lawyer's own
    admin page, instead of needing a separate screen - this is the actual "promoting a
    lawyer" feature the product doc describes."""
    model = LawyerPromotion
    extra = 0
    fields = ("tier", "start_date", "end_date", "active", "notes")


class LawyerEngagementInline(admin.TabularInline):
    model = LawyerEngagementEvent
    extra = 0
    fields = ("event_type", "points", "related_post", "created_at")
    readonly_fields = ("created_at",)


@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "practice_area", "location", "rating", "reviews_count", "verified", "is_sponsored_now", "is_featured_now")
    list_filter = ("verified", "practice_area", "mentorship_available")
    search_fields = ("user__email", "user__first_name", "user__last_name", "firm_name", "practice_area", "location")
    filter_horizontal = ("badges",)
    inlines = [LawyerPromotionInline, LawyerEngagementInline]
    readonly_fields = ("rating", "reviews_count")
    actions = ["recalculate_ratings"]

    @admin.display(boolean=True, description="Sponsored now")
    def is_sponsored_now(self, obj):
        return obj.is_sponsored_now

    @admin.display(boolean=True, description="Featured now")
    def is_featured_now(self, obj):
        return obj.is_featured_now

    @admin.action(description="Recalculate rating from engagement events")
    def recalculate_ratings(self, request, queryset):
        for lawyer in queryset:
            lawyer.recalculate_rating()


@admin.register(LawyerPromotion)
class LawyerPromotionAdmin(admin.ModelAdmin):
    list_display = ("lawyer", "tier", "start_date", "end_date", "active")
    list_filter = ("tier", "active")
    search_fields = ("lawyer__user__email",)


@admin.register(LawyerEngagementEvent)
class LawyerEngagementEventAdmin(admin.ModelAdmin):
    list_display = ("lawyer", "event_type", "points", "created_at")
    list_filter = ("event_type",)


@admin.register(FindLawyerRequest)
class FindLawyerRequestAdmin(admin.ModelAdmin):
    list_display = ("citizen", "category", "location_text", "created_at")
    search_fields = ("citizen__email", "category", "description")
    filter_horizontal = ("matched_lawyers",)


class MentorshipMessageInline(admin.TabularInline):
    model = MentorshipMessage
    extra = 0
    readonly_fields = ("created_at",)


class MentorshipMaterialInline(admin.TabularInline):
    model = MentorshipMaterial
    extra = 0


@admin.register(MentorshipProgramme)
class MentorshipProgrammeAdmin(admin.ModelAdmin):
    list_display = ("title", "lawyer", "weeks", "is_free")
    list_filter = ("is_free",)
    search_fields = ("title", "lawyer__user__email")
    inlines = [MentorshipMaterialInline, MentorshipMessageInline]


admin.site.register(MentorshipEnrollment)
