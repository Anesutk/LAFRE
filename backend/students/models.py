from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class StudentChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_chats", null=True, blank=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    session_id = models.CharField(max_length=80, blank=True, db_index=True)
    title = models.CharField(max_length=180, default="New chat")
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class StudentMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    chat = models.ForeignKey(StudentChat, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    text = models.TextField()
    response_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class StudentDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_documents")
    title = models.CharField(max_length=220)
    file = models.FileField(upload_to="student_documents/%Y/%m/", null=True, blank=True)
    extracted_text = models.TextField(blank=True)
    source_type = models.CharField(max_length=50, default="upload")
    safe_metadata = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class FlashcardDeck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="flashcard_decks")
    title = models.CharField(max_length=180)
    source_chat = models.ForeignKey(StudentChat, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Flashcard(models.Model):
    deck = models.ForeignKey(FlashcardDeck, on_delete=models.CASCADE, related_name="cards")
    front = models.TextField()
    back = models.TextField()
    topic = models.CharField(max_length=120, blank=True)
    difficulty = models.CharField(max_length=20, default="medium")
    source_label = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
