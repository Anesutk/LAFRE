from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from accounts.auth import get_user_from_request, is_admin_user
except Exception:  # pragma: no cover
    get_user_from_request = None
    is_admin_user = None

from .models import (
    AdminNotification,
    DocumentReviewRequest,
    KnowledgeBaseFailure,
    Lawyer,
    LawyerAssignment,
    LawyerBadge,
    LegalMatter,
    PlatformSetting,
    PublicAnnouncement,
    PublicMatterType,
    SupportResource,
)
from .serializers import (
    AdminNotificationSerializer,
    DocumentReviewRequestSerializer,
    KnowledgeBaseFailureSerializer,
    LawyerBadgeSerializer,
    LawyerSerializer,
    PlatformSettingSerializer,
    PublicAnnouncementSerializer,
    PublicMatterTypeSerializer,
    SupportResourceSerializer,
)


class AdminOnlyMixin:
    def require_admin(self, request):
        if not get_user_from_request or not is_admin_user:
            return None, Response({"detail": "Admin authentication is not available."}, status=status.HTTP_403_FORBIDDEN)
        user = get_user_from_request(request)
        if not is_admin_user(user):
            return None, Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
        return user, None

    def require_password(self, request, admin_user):
        password = request.data.get("admin_password") or request.data.get("password") or ""
        if not password:
            return Response({"detail": "Admin password confirmation is required."}, status=status.HTTP_403_FORBIDDEN)
        if not authenticate(username=admin_user.username, password=password):
            return Response({"detail": "Admin password confirmation failed."}, status=status.HTTP_403_FORBIDDEN)
        return None


def _update_model(instance, data: dict[str, Any], allowed: list[str]):
    changed = []
    for field in allowed:
        if field in data:
            setattr(instance, field, data[field])
            changed.append(field)
    if changed:
        instance.save()
    return changed


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


class AdminPublicContentView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        matter_cards = PublicMatterType.objects.all()
        announcements = PublicAnnouncement.objects.all()
        return Response({
            "ok": True,
            "matter_cards": PublicMatterTypeSerializer(matter_cards, many=True).data,
            "announcements": PublicAnnouncementSerializer(announcements, many=True).data,
        })

    def post(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        item_type = request.data.get("type", "matter_card")
        if item_type == "announcement":
            serializer = PublicAnnouncementSerializer(data=request.data)
        else:
            serializer = PublicMatterTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({"ok": True, "item": serializer.data}, status=status.HTTP_201_CREATED)


class AdminMatterCardDetailView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get_object(self, pk):
        return PublicMatterType.objects.filter(pk=pk).first()

    def patch(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Matter card not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PublicMatterTypeSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True, "matter_card": serializer.data})

    def delete(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Matter card not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({"ok": True})


class AdminAnnouncementDetailView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get_object(self, pk):
        return PublicAnnouncement.objects.filter(pk=pk).first()

    def patch(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Announcement not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PublicAnnouncementSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True, "announcement": serializer.data})

    def delete(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Announcement not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({"ok": True})


class AdminResourceAlertsView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        resolved = request.query_params.get("resolved")
        failures = KnowledgeBaseFailure.objects.all()
        if resolved in {"true", "false"}:
            failures = failures.filter(resolved=(resolved == "true"))
        notifications = AdminNotification.objects.all()[:100]
        return Response({
            "ok": True,
            "kb_failures": KnowledgeBaseFailureSerializer(failures[:100], many=True).data,
            "notifications": AdminNotificationSerializer(notifications, many=True).data,
        })


class AdminKBFailureDetailView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        obj = KnowledgeBaseFailure.objects.filter(pk=pk).first()
        if not obj:
            return Response({"detail": "Resource alert not found."}, status=status.HTTP_404_NOT_FOUND)
        changed = _update_model(obj, request.data, ["resolved", "admin_notes", "action_needed"])
        return Response({"ok": True, "changed": changed, "alert": KnowledgeBaseFailureSerializer(obj).data})


class AdminNotificationDetailView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        obj = AdminNotification.objects.filter(pk=pk).first()
        if not obj:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        changed = _update_model(obj, request.data, ["is_read", "priority", "message", "title"])
        return Response({"ok": True, "changed": changed, "notification": AdminNotificationSerializer(obj).data})


class AdminSupportResourcesView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        qs = SupportResource.objects.all()
        q = request.query_params.get("q")
        resource_type = request.query_params.get("type")
        city = request.query_params.get("city")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(notes__icontains=q) | Q(source_note__icontains=q))
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if city:
            qs = qs.filter(city__icontains=city)
        return Response({"ok": True, "resources": SupportResourceSerializer(qs[:200], many=True).data})

    def post(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        serializer = SupportResourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True, "resource": serializer.data}, status=status.HTTP_201_CREATED)


class AdminSupportResourceDetailView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        obj = SupportResource.objects.filter(pk=pk).first()
        if not obj:
            return Response({"detail": "Support resource not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SupportResourceSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True, "resource": serializer.data})


class AdminLawyersView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        qs = Lawyer.objects.prefetch_related("badges").all()
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(full_name__icontains=q) | Q(firm_name__icontains=q) | Q(city__icontains=q))
        return Response({
            "ok": True,
            "lawyers": LawyerSerializer(qs[:200], many=True).data,
            "badges": LawyerBadgeSerializer(LawyerBadge.objects.all(), many=True).data,
        })

    def post(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        data = request.data.copy()
        badge_ids = data.pop("badge_ids", []) or data.pop("badges", [])
        serializer = LawyerSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        lawyer = serializer.save()
        if badge_ids:
            lawyer.badges.set(LawyerBadge.objects.filter(id__in=badge_ids))
        return Response({"ok": True, "lawyer": LawyerSerializer(lawyer).data}, status=status.HTTP_201_CREATED)


class AdminLawyerDetailView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        lawyer = Lawyer.objects.filter(pk=pk).first()
        if not lawyer:
            return Response({"detail": "Lawyer not found."}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        badge_ids = data.pop("badge_ids", None)
        serializer = LawyerSerializer(lawyer, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        lawyer = serializer.save()
        if badge_ids is not None:
            lawyer.badges.set(LawyerBadge.objects.filter(id__in=badge_ids))
        return Response({"ok": True, "lawyer": LawyerSerializer(lawyer).data})


class AdminDocumentQueueView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        qs = DocumentReviewRequest.objects.select_related("document", "assigned_lawyer", "user").all()
        req_status = request.query_params.get("status")
        if req_status:
            qs = qs.filter(status=req_status)
        return Response({"ok": True, "document_reviews": DocumentReviewRequestSerializer(qs[:200], many=True).data})


class AdminDocumentReviewDetailView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, pk):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        obj = DocumentReviewRequest.objects.filter(pk=pk).first()
        if not obj:
            return Response({"detail": "Document review request not found."}, status=status.HTTP_404_NOT_FOUND)
        allowed = ["status", "assigned_lawyer", "admin_note", "lawyer_note"]
        changed = []
        if "assigned_lawyer" in request.data:
            lawyer = Lawyer.objects.filter(pk=request.data.get("assigned_lawyer")).first()
            obj.assigned_lawyer = lawyer
            if lawyer and obj.status == DocumentReviewRequest.Status.PENDING_ADMIN:
                obj.status = DocumentReviewRequest.Status.ASSIGNED_LAWYER
            changed += ["assigned_lawyer", "status"]
            if lawyer:
                LawyerAssignment.objects.get_or_create(
                    lawyer=lawyer,
                    document_review=obj,
                    defaults={"matter": obj.document.matter, "assigned_by": admin_user, "notes": request.data.get("admin_note", "")},
                )
        for field in ["status", "admin_note", "lawyer_note"]:
            if field in request.data:
                setattr(obj, field, request.data[field])
                changed.append(field)
        obj.save()
        return Response({"ok": True, "changed": list(set(changed)), "document_review": DocumentReviewRequestSerializer(obj).data})


class AdminPlatformSettingsView(AdminOnlyMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        return Response({"ok": True, "settings": PlatformSettingSerializer(PlatformSetting.objects.all(), many=True).data})

    def post(self, request):
        return self.patch(request)

    def patch(self, request):
        admin_user, error = self.require_admin(request)
        if error:
            return error
        password_error = self.require_password(request, admin_user)
        if password_error:
            return password_error
        settings_payload = request.data.get("settings") or []
        updated = []
        for item in settings_payload:
            key = item.get("key")
            if not key:
                continue
            obj, _created = PlatformSetting.objects.get_or_create(
                key=key,
                defaults={"label": item.get("label") or key.replace("_", " ").title()},
            )
            obj.label = item.get("label", obj.label)
            obj.value = item.get("value", obj.value)
            if "is_public" in item:
                obj.is_public = _parse_bool(item.get("is_public"))
            obj.save()
            updated.append(obj)
        return Response({"ok": True, "settings": PlatformSettingSerializer(updated or PlatformSetting.objects.all(), many=True).data})
