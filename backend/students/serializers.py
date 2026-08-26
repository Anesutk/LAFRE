from rest_framework import serializers


class StudentAskSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    history = serializers.ListField(child=serializers.DictField(), required=False, default=[])
    context_texts = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    conversation_summary = serializers.CharField(required=False, allow_blank=True, default="")
    active_documents = serializers.ListField(child=serializers.DictField(), required=False, default=[])
    # "auto" preserves the earlier student-agent behaviour: the agent decides the correct mode/tool.
    # Manual buttons remain shortcuts, but they do not remove automatic routing.
    mode = serializers.CharField(required=False, allow_blank=True, default="auto")


class AssignmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    assignment_type = serializers.CharField(required=False, allow_blank=True, default="assignment_help")
    instruction = serializers.CharField(required=False, allow_blank=True, default="")



class StudentAccessRequestSerializer(serializers.Serializer):
    request_type = serializers.ChoiceField(
        choices=[
            ("messages", "More messages"),
            ("documents", "More document reads"),
            ("uploads", "More uploads"),
            ("student_access", "Student access review"),
        ],
        default="messages",
    )
    amount = serializers.IntegerField(min_value=1, max_value=500, default=20)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1200)
