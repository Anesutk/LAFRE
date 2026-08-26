from decimal import Decimal
from uuid import uuid4

from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.auth import get_user_from_request
from accounts.models import UserProfile
from .document_service import (
    assess_flags,
    create_pdf_file,
    document_text,
    generate_title,
    next_steps,
    summary_for,
)
from .models import GeneratedDocument, LawyerReviewRequest, Matter, MatterEvidence, SimulatedPayment
from .pathways import get_pathway, list_pathways
from .serializers import (
    AskMatterSerializer,
    CreateMatterSerializer,
    EvidenceSerializer,
    LoginSerializer,
    MatterSerializer,
    PaymentSimulationSerializer,
    RegisterSerializer,
    ReviewRequestCreateSerializer,
    LawyerReviewSerializer,
    token_payload,
)


def require_citizen(request):
    user = get_user_from_request(request)
    if not user:
        return None, Response({'detail': 'Sign in to LAFRE Citizens first.'}, status=401)
    profile = getattr(user, 'lafre_profile', None)
    if not profile or profile.role != UserProfile.Role.CITIZEN:
        return None, Response({'detail': 'This endpoint is for citizen accounts.'}, status=403)
    return user, None


@api_view(['POST'])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(token_payload(user), status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(token_payload(serializer.validated_data['user']))


@api_view(['GET'])
def me_view(request):
    from .serializers import UserSerializer
    user, error = require_citizen(request)
    if error:
        return error
    return Response(UserSerializer(user).data)


@api_view(['GET'])
def pathways_view(request):
    return Response(list_pathways())


@api_view(['GET'])
def pathway_detail_view(request, key):
    pathway = get_pathway(key)
    if not pathway:
        return Response({'detail': 'Pathway not found.'}, status=404)
    return Response(pathway)


class MatterListCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, error = require_citizen(request)
        if error:
            return error
        matters = Matter.objects.filter(user=user)
        return Response(MatterSerializer(matters, many=True, context={'request': request}).data)

    def post(self, request):
        user, error = require_citizen(request)
        if error:
            return error
        serializer = CreateMatterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pathway_key = serializer.validated_data['pathway_key']
        answers = serializer.validated_data.get('answers') or {}
        pathway = get_pathway(pathway_key)
        title = generate_title(pathway_key, answers)
        flags = assess_flags(pathway_key, answers)
        status_value = 'needs_review' if flags else 'document_generated'
        if pathway_key == 'contract-of-sale':
            status_value = 'needs_review'

        matter = Matter.objects.create(
            user=user,
            pathway_key=pathway_key,
            pathway_title=pathway['title'],
            title=title,
            risk_level=pathway.get('risk_level', 'Medium'),
            answers=answers,
            summary=summary_for(pathway_key, answers),
            next_steps=next_steps(pathway_key),
            flags=flags,
            status=status_value,
        )
        create_generated_document(matter)
        return Response(MatterSerializer(matter, context={'request': request}).data, status=201)


class MatterDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_object(self, request, pk):
        user, error = require_citizen(request)
        if error:
            raise Http404
        try:
            return Matter.objects.get(pk=pk, user=user)
        except Matter.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        matter = self.get_object(request, pk)
        return Response(MatterSerializer(matter, context={'request': request}).data)

    def patch(self, request, pk):
        matter = self.get_object(request, pk)
        answers = request.data.get('answers')
        if isinstance(answers, dict):
            matter.answers.update(answers)
            matter.title = generate_title(matter.pathway_key, matter.answers)
            matter.summary = summary_for(matter.pathway_key, matter.answers)
            matter.flags = assess_flags(matter.pathway_key, matter.answers)
            matter.next_steps = next_steps(matter.pathway_key)
            matter.status = 'needs_review' if matter.flags or matter.pathway_key == 'contract-of-sale' else 'document_generated'
        if request.data.get('title'):
            matter.title = request.data['title']
        matter.save()
        create_generated_document(matter)
        return Response(MatterSerializer(matter, context={'request': request}).data)


def create_generated_document(matter):
    version = (matter.documents.count() or 0) + 1
    doc = GeneratedDocument.objects.create(
        matter=matter,
        document_type=matter.pathway_title,
        version=version,
        content=document_text(matter.pathway_key, matter.answers),
    )
    create_pdf_file(doc)
    return doc


@api_view(['POST'])
def generate_document_view(request, pk):
    user, error = require_citizen(request)
    if error:
        return error
    try:
        matter = Matter.objects.get(pk=pk, user=user)
    except Matter.DoesNotExist:
        raise Http404
    doc = create_generated_document(matter)
    return Response({'document_id': doc.id, 'pdf_url': request.build_absolute_uri(doc.pdf_file.url)})


@api_view(['GET'])
def download_pdf_view(request, document_id):
    user, error = require_citizen(request)
    if error:
        return error
    try:
        doc = GeneratedDocument.objects.get(pk=document_id, matter__user=user)
    except GeneratedDocument.DoesNotExist:
        raise Http404
    if not doc.pdf_file:
        create_pdf_file(doc)
    return FileResponse(doc.pdf_file.open('rb'), as_attachment=False, filename=f'{doc.matter.title}.pdf')


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_evidence_view(request, pk):
    user, error = require_citizen(request)
    if error:
        return error
    try:
        matter = Matter.objects.get(pk=pk, user=user)
    except Matter.DoesNotExist:
        raise Http404
    serializer = EvidenceSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    evidence = MatterEvidence.objects.create(
        matter=matter,
        uploaded_by=user,
        evidence_type=serializer.validated_data.get('evidence_type', 'other'),
        description=serializer.validated_data.get('description', ''),
        file=serializer.validated_data['file'],
    )
    return Response(EvidenceSerializer(evidence, context={'request': request}).data, status=201)


@api_view(['POST'])
def request_review_view(request, pk):
    user, error = require_citizen(request)
    if error:
        return error
    try:
        matter = Matter.objects.get(pk=pk, user=user)
    except Matter.DoesNotExist:
        raise Http404
    serializer = ReviewRequestCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    pathway = get_pathway(matter.pathway_key)
    fee = Decimal(str(pathway.get('fixed_review_fee', '3.00')))
    review = LawyerReviewRequest.objects.create(
        matter=matter,
        requested_by=user,
        review_type=serializer.validated_data['review_type'],
        fixed_fee=fee,
        payment_status='pending',
        review_status='payment_pending',
    )
    return Response(LawyerReviewSerializer(review).data, status=201)


@api_view(['POST'])
def simulate_payment_view(request, review_id):
    user, error = require_citizen(request)
    if error:
        return error
    try:
        review = LawyerReviewRequest.objects.get(pk=review_id, requested_by=user)
    except LawyerReviewRequest.DoesNotExist:
        raise Http404
    serializer = PaymentSimulationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payment = SimulatedPayment.objects.create(
        review_request=review,
        phone_number=serializer.validated_data['phone_number'],
        amount=review.fixed_fee,
        reference=f'LAFRE-{uuid4().hex[:10].upper()}',
        status='success',
    )
    review.payment_status = 'paid'
    review.review_status = 'submitted'
    review.save()
    matter = review.matter
    matter.status = 'sent_to_lawyer'
    matter.save()
    return Response({
        'status': 'success',
        'reference': payment.reference,
        'review': LawyerReviewSerializer(review).data,
    })


@api_view(['POST'])
def ask_matter_view(request, pk):
    user, error = require_citizen(request)
    if error:
        return error
    try:
        matter = Matter.objects.get(pk=pk, user=user)
    except Matter.DoesNotExist:
        raise Http404
    serializer = AskMatterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    q = serializer.validated_data['question']
    answer = (
        f"Based on your saved matter '{matter.title}', here is legal information, not legal advice. "
        f"Matter summary: {matter.summary} "
        f"Next practical step: {matter.next_steps[0] if matter.next_steps else 'review your document carefully'}. "
        "For legal advice, certification, representation, or validation, send the matter to a registered legal practitioner."
    )
    return Response({'question': q, 'answer': answer})
