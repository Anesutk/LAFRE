from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.auth import get_user_from_request
from .models import DocumentReviewRequest, Lawyer
from .serializers import DocumentReviewRequestSerializer


def require_lawyer(request):
    user = get_user_from_request(request)
    if not user:
        return None, None, Response({"ok": False, "detail": "Sign in to the lawyer portal first."}, status=401)
    profile = getattr(user, "lafre_profile", None)
    if not profile or not profile.can_access_lawyer_portal or not profile.is_active_for_platform():
        return user, None, Response({"ok": False, "detail": "This account does not have active lawyer portal access."}, status=403)
    lawyer = Lawyer.objects.filter(user=user, is_active=True).first()
    if not lawyer:
        return user, None, Response({"ok": False, "detail": "No lawyer profile is linked to this account yet. Contact the administrator."}, status=403)
    return user, lawyer, None


class LawyerDashboardView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, lawyer, error = require_lawyer(request)
        if error:
            return error
        reviews = DocumentReviewRequest.objects.filter(assigned_lawyer=lawyer).order_by("-updated_at")
        return Response({
            "ok": True,
            "lawyer": {"id": lawyer.id, "full_name": lawyer.full_name, "verified": lawyer.verified, "badges": [b.name for b in lawyer.badges.all()]},
            "reviews": DocumentReviewRequestSerializer(reviews, many=True).data,
        })


class LawyerReviewDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk: int):
        user, lawyer, error = require_lawyer(request)
        if error:
            return error
        review = DocumentReviewRequest.objects.filter(id=pk, assigned_lawyer=lawyer).first()
        if not review:
            return Response({"ok": False, "detail": "Review not found."}, status=404)
        return Response({"ok": True, "review": DocumentReviewRequestSerializer(review).data})

    def patch(self, request, pk: int):
        user, lawyer, error = require_lawyer(request)
        if error:
            return error
        review = DocumentReviewRequest.objects.filter(id=pk, assigned_lawyer=lawyer).first()
        if not review:
            return Response({"ok": False, "detail": "Review not found."}, status=404)
        if "lawyer_note" in request.data:
            review.lawyer_note = request.data["lawyer_note"]
        if "status" in request.data:
            review.status = request.data["status"]
        review.save()
        return Response({"ok": True, "review": DocumentReviewRequestSerializer(review).data})


class LawyerReviewUploadView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, pk: int):
        user, lawyer, error = require_lawyer(request)
        if error:
            return error
        review = DocumentReviewRequest.objects.filter(id=pk, assigned_lawyer=lawyer).first()
        if not review:
            return Response({"ok": False, "detail": "Review not found."}, status=404)
        if request.FILES.get("reviewed_file"):
            review.reviewed_file = request.FILES["reviewed_file"]
        if request.FILES.get("signed_or_stamped_file"):
            review.signed_or_stamped_file = request.FILES["signed_or_stamped_file"]
        if request.data.get("lawyer_note"):
            review.lawyer_note = request.data["lawyer_note"]
        review.status = request.data.get("status") or "reviewed"
        review.save()
        return Response({"ok": True, "review": DocumentReviewRequestSerializer(review).data})
