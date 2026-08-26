from django.contrib import admin
from .models import Flashcard, FlashcardDeck, StudentChat, StudentDocument, StudentMessage

class StudentMessageInline(admin.TabularInline):
    model = StudentMessage
    extra = 0
    readonly_fields = ("created_at",)

@admin.register(StudentChat)
class StudentChatAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "updated_at")
    search_fields = ("title", "user__email")
    inlines = [StudentMessageInline]

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "source_type", "active", "updated_at")
    list_filter = ("source_type", "active")
    search_fields = ("title", "user__email", "extracted_text")

class FlashcardInline(admin.TabularInline):
    model = Flashcard
    extra = 0

@admin.register(FlashcardDeck)
class FlashcardDeckAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "updated_at")
    search_fields = ("title", "user__email")
    inlines = [FlashcardInline]
