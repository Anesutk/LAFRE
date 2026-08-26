from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from accounts.models import ManualAccessToken, UserProfile
from .models import Matter, GeneratedDocument, MatterEvidence, LawyerReviewRequest
from .pathways import get_pathway


def split_name(full_name: str):
    clean = (full_name or '').strip()
    if not clean:
        return '', ''
    first, *rest = clean.split()
    return first, ' '.join(rest)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'role']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email or obj.username

    def get_phone(self, obj):
        profile = getattr(obj, 'lafre_profile', None)
        return getattr(profile, 'phone', '') if profile else ''

    def get_role(self, obj):
        return 'citizen'


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=40, required=False, allow_blank=True)
    password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)

    def validate_email(self, value):
        clean = (value or '').strip().lower()
        if User.objects.filter(username__iexact=clean).exists() or User.objects.filter(email__iexact=clean).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return clean

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        first, last = split_name(validated_data['full_name'])
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=first,
            last_name=last,
        )
        # Citizens pathway account: no verification/admin approval required in this v1.
        UserProfile.objects.create(
            user=user,
            role=UserProfile.Role.CITIZEN,
            requested_role=UserProfile.Role.CITIZEN,
            status=UserProfile.Status.APPROVED,
            phone=(validated_data.get('phone') or '').strip(),
            auth_provider=UserProfile.AuthProvider.EMAIL,
            email_verified=False,
            can_use_civilian=True,
            can_generate_documents=True,
            can_request_lawyer=True,
            daily_upload_limit=10,
            monthly_upload_limit=120,
            daily_document_limit=10,
            monthly_document_limit=100,
            approved_at=timezone.now(),
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = (attrs['email'] or '').strip().lower()
        user = authenticate(username=email, password=attrs['password'])
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'})
        profile = getattr(user, 'lafre_profile', None)
        if not profile or profile.role != UserProfile.Role.CITIZEN:
            raise serializers.ValidationError({'detail': 'This sign-in page is for citizen pathway accounts.'})
        attrs['user'] = user
        return attrs


def token_payload(user):
    token = ManualAccessToken.objects.create(user=user)
    return {
        'token': str(token.token),
        # access/refresh are included only so older citizen mock frontend code also works.
        'access': str(token.token),
        'refresh': str(token.token),
        'user': UserSerializer(user).data,
    }


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedDocument
        fields = ['id', 'document_type', 'version', 'content', 'pdf_url', 'created_at']

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if obj.pdf_file and request:
            return request.build_absolute_uri(f'/api/citizens/documents/{obj.id}/download-pdf/')
        return None


class EvidenceSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = MatterEvidence
        fields = ['id', 'evidence_type', 'description', 'file', 'file_url', 'created_at']
        read_only_fields = ['id', 'file_url', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class LawyerReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerReviewRequest
        fields = ['id', 'review_type', 'fixed_fee', 'payment_status', 'review_status', 'mock_lawyer_name', 'lawyer_notes', 'created_at', 'updated_at']


class MatterSerializer(serializers.ModelSerializer):
    documents = GeneratedDocumentSerializer(many=True, read_only=True)
    evidence = EvidenceSerializer(many=True, read_only=True)
    review_requests = LawyerReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Matter
        fields = ['id', 'pathway_key', 'pathway_title', 'title', 'status', 'risk_level', 'summary', 'next_steps', 'flags', 'answers', 'documents', 'evidence', 'review_requests', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateMatterSerializer(serializers.Serializer):
    pathway_key = serializers.CharField(max_length=80)
    answers = serializers.JSONField(required=False)

    def validate_pathway_key(self, value):
        if not get_pathway(value):
            raise serializers.ValidationError('Unknown pathway.')
        return value


class AskMatterSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)


class ReviewRequestCreateSerializer(serializers.Serializer):
    review_type = serializers.ChoiceField(choices=['document_check', 'certification', 'consultation'], default='document_check')


class PaymentSimulationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=40)
    pin = serializers.CharField(max_length=12, write_only=True)
