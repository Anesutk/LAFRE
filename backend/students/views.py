from __future__ import annotations

import json
import queue
import re
import threading
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile

from django.db import transaction
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.core import signing
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.auth import get_user_from_request
from .generation import clean_display_title, generate_chat_title, safe_title
from . import answer_agent


class AnswerGenerationError(Exception):
    """Raised when the answer agent itself fails. No legacy keyword-routed pipeline exists to
    fall back to anymore (removed on purpose) - the view catches this and returns a clean,
    honest error to the student instead of a degraded answer or an unhandled 500.
    """


def generate_answer_with_fallback(*, user, question, depth, requested_view, history_summary, prior_sources, progress_callback=None):
    """Despite the name (kept so call sites didn't need renaming), there is no fallback
    pipeline anymore - this calls the agent and raises AnswerGenerationError on failure.
    """
    result = answer_agent.generate_agentic_answer(
        user=user, question=question, depth=depth,
        history_summary=history_summary, prior_sources=prior_sources,
        progress_callback=progress_callback,
    )
    if result is None:
        raise AnswerGenerationError("The study assistant could not produce an answer for that question.")
    return result
from .models import Flashcard, FlashcardDeck, StudentChat, StudentDocument, StudentMessage


def api_error(message: str, status_code: int = 400, errors: dict | None = None, **extra):
    payload = {"ok": False, "success": False, "message": message, "detail": message, "errors": errors or {}}
    payload.update(extra)
    return Response(payload, status=status_code)


def require_student(request):
    user = get_user_from_request(request)
    if not user:
        return None, None, api_error("Sign in to LAFRE Student first.", 401)
    profile = getattr(user, "lafre_profile", None)
    if not profile or not profile.can_use_student:
        return user, profile, api_error("This account does not have LAFRE Student access.", 403)
    if not profile.is_active_for_platform():
        return user, profile, api_error(
            "Your LAFRE Student account is waiting for admin approval.",
            403,
            redirect_to="/pending",
        )
    return user, profile, None


GUEST_MESSAGE_LIMIT = 3


def request_session_id(request):
    return (request.headers.get("X-Session-ID") or request.META.get("HTTP_X_SESSION_ID") or "").strip()[:80]


def chat_key(chat):
    return str(chat.public_id)


def find_chat(request, key, user=None, claim_guest=False):
    if not key:
        return None
    queryset = StudentChat.objects.all()
    try:
        chat = queryset.filter(public_id=key).first()
    except (TypeError, ValueError):
        chat = None
    if not chat and str(key).isdigit():
        chat = queryset.filter(id=int(key)).first()
    if not chat:
        return None
    session_id = request_session_id(request)
    owns_chat = bool(user and chat.user_id == user.id)
    guest_owns_chat = bool(not chat.user_id and session_id and chat.session_id == session_id)
    if not (owns_chat or guest_owns_chat):
        return None
    if claim_guest and user and not chat.user_id:
        chat.user = user
        chat.save(update_fields=["user", "updated_at"])
    return chat


def extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
        root = ET.fromstring(xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for p in root.findall(".//w:p", ns):
            text = "".join(t.text or "" for t in p.findall(".//w:t", ns))
            if text.strip():
                paragraphs.append(text.strip())
        return "\n".join(paragraphs)
    except Exception:
        return ""


def extract_text_from_upload(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    try:
        raw = uploaded_file.read()
        uploaded_file.seek(0)
    except Exception:
        return ""
    if name.endswith((".txt", ".md", ".csv")):
        return raw.decode("utf-8", errors="ignore")
    if name.endswith(".docx"):
        tmp = Path(tempfile.gettempdir()) / f"lafre_{slugify(uploaded_file.name)[:50]}.docx"
        tmp.write_bytes(raw)
        return extract_docx_text(tmp)
    if name.endswith(".pdf"):
        try:
            import pypdf  # type: ignore
            tmp = Path(tempfile.gettempdir()) / f"lafre_{slugify(uploaded_file.name)[:50]}.pdf"
            tmp.write_bytes(raw)
            reader = pypdf.PdfReader(str(tmp))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return "PDF uploaded. Text extraction was not available in this environment. The file is still stored for viewing."
    return raw.decode("utf-8", errors="ignore")[:20000]


def title_for_chat(prompt: str) -> str:
    return generate_chat_title(prompt)


def normalise_depth(value: str | None) -> str:
    value = (value or "normal").strip().lower()
    return "thinking" if value in {"thinking", "detailed", "deep", "long"} else "normal"


def clean_history_summary(chat: StudentChat | None) -> str:
    if not chat:
        return ""
    messages = list(chat.messages.order_by("-created_at")[:12])
    messages.reverse()
    parts = []
    for message in messages:
        text = re.sub(r"\s+", " ", message.text or "").strip()[:1400]
        if text:
            parts.append(f"{message.role}: {text}")
    return "\n".join(parts)


def recent_response_sources(chat: StudentChat | None) -> list[dict]:
    """Return source/document objects from recent assistant messages in this chat.

    This lets a follow-up like “give me the documents” reuse the documents/sources
    already used in the previous answer instead of doing an unrelated fresh search.
    """
    if not chat:
        return []
    seen = set()
    rows: list[dict] = []
    messages = chat.messages.filter(role="assistant").order_by("-created_at")[:4]
    for message in messages:
        payload = message.response_payload or {}
        if not isinstance(payload, dict):
            continue
        for item in (payload.get("documents") or []) + (payload.get("source_badges") or []):
            if not isinstance(item, dict):
                continue
            key = (item.get("title"), item.get("open_url"), item.get("download_url"), item.get("kind"))
            if key in seen:
                continue
            seen.add(key)
            rows.append(item)
            if len(rows) >= 12:
                return rows
    return rows


class StudentAskView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = get_user_from_request(request)
        profile = getattr(user, "lafre_profile", None) if user else None
        if user and (not profile or not profile.can_use_student or not profile.is_active_for_platform()):
            _, _, error = require_student(request)
            return error
        prompt = (request.data.get("prompt") or request.data.get("question") or "").strip()
        if not prompt:
            return api_error("Type a legal-study question first.", 400, errors={"prompt": ["Question is required."]})
        chat_id = request.data.get("chat_id")
        chat = find_chat(request, chat_id, user=user, claim_guest=True) if chat_id else None
        guest_messages = 0
        if not user:
            session_id = request_session_id(request)
            guest_messages = StudentMessage.objects.filter(
                chat__user__isnull=True, chat__session_id=session_id, role="user"
            ).count()
        if not user and guest_messages >= GUEST_MESSAGE_LIMIT:
            return api_error(
                "Sign in to continue this chat.", 401,
                mode="login_required",
                chat_id=chat_key(chat) if chat else "",
                chat_url=f"/chat?chat={chat_key(chat)}" if chat else "/login",
            )
        if profile and profile.daily_message_limit and profile.remaining_messages() <= 0:
            return api_error("Daily message limit reached.", 429, mode="limit_reached")

        is_new_chat = False
        if not chat:
            chat = StudentChat.objects.create(user=user, session_id=request_session_id(request), title=title_for_chat(prompt))
            is_new_chat = True
        prior_sources = recent_response_sources(chat)
        history_summary = clean_history_summary(chat)
        StudentMessage.objects.create(chat=chat, role="user", text=prompt)

        answer_depth = normalise_depth(request.data.get("answer_style") or request.data.get("depth"))
        requested_view = request.data.get("mode") or request.data.get("view") or "auto"
        try:
            payload = generate_answer_with_fallback(
                user=user,
                question=prompt,
                depth=answer_depth,
                requested_view=requested_view,
                history_summary=history_summary,
                prior_sources=prior_sources,
            )
        except AnswerGenerationError:
            return api_error(
                "The study assistant couldn't produce an answer just now - please try again in a moment.",
                503,
                mode="generation_failed",
            )
        StudentMessage.objects.create(chat=chat, role="assistant", text=payload["markdown"], response_payload=payload)
        if is_new_chat or chat.title == "New chat":
            chat.title = title_for_chat(prompt)
            chat.save(update_fields=["title", "updated_at"])
        if profile and profile.daily_message_limit:
            profile.consume_message()
        return Response({
            "ok": True,
            "success": True,
            "chat_id": chat_key(chat),
            "chat": {"id": chat_key(chat), "title": chat.title, "updated_at": chat.updated_at, "url": f"/chat?chat={chat_key(chat)}"},
            "response": payload,
        })


class StudentAskStreamView(APIView):
    """Same behaviour as StudentAskView (guest limits, chat persistence, history
    context, daily limits) but delivers the answer as an SSE token stream so the
    frontend can render progressively instead of waiting for the full response.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = get_user_from_request(request)
        profile = getattr(user, "lafre_profile", None) if user else None
        if user and (not profile or not profile.can_use_student or not profile.is_active_for_platform()):
            _, _, error = require_student(request)
            return error
        prompt = (request.data.get("prompt") or request.data.get("question") or "").strip()
        if not prompt:
            return api_error("Type a legal-study question first.", 400, errors={"prompt": ["Question is required."]})
        chat_id = request.data.get("chat_id")
        chat = find_chat(request, chat_id, user=user, claim_guest=True) if chat_id else None
        if not user:
            session_id = request_session_id(request)
            guest_messages = StudentMessage.objects.filter(
                chat__user__isnull=True, chat__session_id=session_id, role="user"
            ).count()
            if guest_messages >= GUEST_MESSAGE_LIMIT:
                return api_error(
                    "Sign in to continue this chat.", 401,
                    mode="login_required",
                    chat_id=chat_key(chat) if chat else "",
                    chat_url=f"/chat?chat={chat_key(chat)}" if chat else "/login",
                )
        if profile and profile.daily_message_limit and profile.remaining_messages() <= 0:
            return api_error("Daily message limit reached.", 429, mode="limit_reached")

        answer_depth = normalise_depth(request.data.get("answer_style") or request.data.get("depth"))
        requested_view = request.data.get("mode") or request.data.get("view") or "auto"

        is_new_chat = False
        if not chat:
            chat = StudentChat.objects.create(user=user, session_id=request_session_id(request), title=title_for_chat(prompt))
            is_new_chat = True
        prior_sources = recent_response_sources(chat)
        history_summary = clean_history_summary(chat)
        StudentMessage.objects.create(chat=chat, role="user", text=prompt)

        def event_stream():
            # Generation runs in a background thread so the HTTP response (and this
            # generator) can start immediately and forward REAL progress events the moment
            # Strands actually invokes each tool - not a fake delay tacked onto the end
            # after the full answer is already sitting in memory, which is what made
            # streaming feel broken before: the response used to not even begin until the
            # whole multi-tool-call agent turn had already finished.
            progress_queue: "queue.Queue" = queue.Queue()
            result_holder: dict = {}

            def on_progress(label: str):
                progress_queue.put(("status", label))

            def run_generation():
                try:
                    result_holder["payload"] = generate_answer_with_fallback(
                        user=user,
                        question=prompt,
                        depth=answer_depth,
                        requested_view=requested_view,
                        history_summary=history_summary,
                        prior_sources=prior_sources,
                        progress_callback=on_progress,
                    )
                except Exception as exc:  # noqa: BLE001 - forwarded to the client below
                    result_holder["error"] = exc
                finally:
                    # This thread opens its own DB connection (used by search_sources'
                    # ORM queries) that Django won't clean up automatically since it isn't
                    # a request-response thread - close it explicitly to avoid leaking
                    # connections across requests.
                    from django.db import connections as _connections
                    _connections.close_all()
                    progress_queue.put(("__done__", None))

            worker = threading.Thread(target=run_generation, daemon=True)
            worker.start()

            sent_statuses = set()
            while True:
                kind, value = progress_queue.get()
                if kind == "__done__":
                    break
                if kind == "status" and value not in sent_statuses:
                    sent_statuses.add(value)
                    yield f"data: {json.dumps({'type': 'status', 'text': value})}\n\n"
            worker.join()

            if "error" in result_holder:
                error_message = "The study assistant couldn't produce an answer just now - please try again."
                yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
                return

            payload = result_holder["payload"]
            StudentMessage.objects.create(chat=chat, role="assistant", text=payload["markdown"], response_payload=payload)
            if is_new_chat or chat.title == "New chat":
                chat.title = title_for_chat(prompt)
                chat.save(update_fields=["title", "updated_at"])
            if profile and profile.daily_message_limit:
                profile.consume_message()
            chat_payload = {"id": chat_key(chat), "title": chat.title, "url": f"/chat?chat={chat_key(chat)}"}

            text = payload["markdown"]
            meta = {k: v for k, v in payload.items() if k != "markdown"}
            meta["chat"] = chat_payload
            meta["chat_id"] = chat_payload["id"]
            yield f"data: {json.dumps({'type': 'meta', 'payload': meta})}\n\n"
            # The full answer is ready at this point (real streaming happened above, via
            # status events during generation) - reveal the text in small word-groups for a
            # smooth read-in rather than a single jump, still far faster than before since
            # there's no artificial per-chunk sleep stacked on top of the wait.
            chunks = re.findall(r"\S+\s*", text)
            for i in range(0, len(chunks), 4):
                piece = "".join(chunks[i:i + 4])
                if piece:
                    yield f"data: {json.dumps({'type': 'token', 'text': piece})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'payload': {**payload, 'chat': chat_payload, 'chat_id': chat_payload['id']}})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        # Most proxies (Render's included) gzip/buffer responses by default, which silently
        # defeats SSE: the browser gets nothing until the whole body is ready, indistinguishable
        # from "streaming isn't working". These headers tell intermediate proxies/browsers not
        # to buffer or compress this response.
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"  # nginx-style proxies
        response["Content-Encoding"] = "identity"  # stop gzip from buffering the whole body
        return response


class AssignmentUploadView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user, profile, error = require_student(request)
        if error:
            return error
        if profile.daily_upload_limit and profile.remaining_uploads() <= 0:
            return api_error("Daily upload limit reached.", 429)
        uploaded = request.FILES.get("file")
        if not uploaded:
            return api_error("Choose a file to upload.", 400, errors={"file": ["File is required."]})
        title = safe_title(request.data.get("title") or uploaded.name)
        text = extract_text_from_upload(uploaded)
        doc = StudentDocument.objects.create(
            user=user,
            title=title,
            file=uploaded,
            extracted_text=text[:200000],
            safe_metadata={"original_label": title},
        )
        if profile.daily_upload_limit:
            profile.consume_upload()
        return Response({
            "ok": True,
            "success": True,
            "document": {
                "id": doc.id,
                "title": doc.title,
                "open_url": f"/api/students/documents/{doc.id}/view/",
                "download_url": f"/api/students/documents/{doc.id}/download/",
            },
        })


class StudentDocumentListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, profile, error = require_student(request)
        if error:
            return error
        docs = StudentDocument.objects.filter(user=user, active=True).order_by("-updated_at")
        rows = []
        for d in docs:
            file_size = 0
            file_type = "Document"
            if d.file:
                try:
                    file_size = d.file.size
                except Exception:
                    file_size = 0
                suffix = Path(d.file.name).suffix.replace(".", "").upper()
                file_type = suffix or file_type
            rows.append({
                "id": d.id,
                "title": clean_display_title(d.title),
                "download_name": safe_title(d.title),
                "type": file_type,
                "size": file_size,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
                "excerpt": (d.extracted_text or "")[:260],
                "open_url": f"/api/students/documents/{d.id}/view/",
                "download_url": f"/api/students/documents/{d.id}/download/",
            })
        return Response({"ok": True, "success": True, "documents": rows})


class StudentDocumentDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def delete(self, request, pk: int):
        user, profile, error = require_student(request)
        if error:
            return error
        doc = StudentDocument.objects.filter(id=pk, user=user, active=True).first()
        if not doc:
            return api_error("Document not found.", 404)
        doc.active = False
        doc.save(update_fields=["active", "updated_at"])
        return Response({"ok": True, "success": True})


class StudentChatListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = get_user_from_request(request)
        if user:
            chats = StudentChat.objects.filter(user=user).order_by("-updated_at")[:100]
        else:
            session_id = request_session_id(request)
            chats = StudentChat.objects.filter(user__isnull=True, session_id=session_id).order_by("-updated_at")[:100]
        return Response({"ok": True, "success": True, "chats": [{"id": chat_key(c), "title": c.title, "updated_at": c.updated_at, "url": f"/chat?chat={chat_key(c)}"} for c in chats]})


class StudentChatDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk: int):
        user = get_user_from_request(request)
        chat = find_chat(request, pk, user=user, claim_guest=bool(user))
        if not chat:
            return api_error("Chat not found.", 404)
        return Response({
            "ok": True,
            "success": True,
            "chat": {
                "id": chat_key(chat),
                "title": chat.title,
                "messages": [
                    {"role": m.role, "text": m.text, "response": m.response_payload, "created_at": m.created_at}
                    for m in chat.messages.all()
                ],
            },
        })

    def patch(self, request, pk: int):
        """Rename a chat. Powers the chat header's "..." menu."""
        user = get_user_from_request(request)
        chat = find_chat(request, pk, user=user, claim_guest=bool(user))
        if not chat:
            return api_error("Chat not found.", 404)
        title = (request.data.get("title") or "").strip()
        if not title:
            return api_error("A chat title is required.", 400, errors={"title": ["Title is required."]})
        chat.title = title[:120]
        chat.save(update_fields=["title", "updated_at"])
        return Response({"ok": True, "success": True, "chat": {"id": chat_key(chat), "title": chat.title}})

    def delete(self, request, pk: int):
        """Delete a chat. Powers the chat header's "..." menu."""
        user = get_user_from_request(request)
        chat = find_chat(request, pk, user=user, claim_guest=bool(user))
        if not chat:
            return api_error("Chat not found.", 404)
        chat.delete()
        return Response({"ok": True, "success": True, "deleted": True})


class FlashcardDeckListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, profile, error = require_student(request)
        if error:
            return error
        decks = FlashcardDeck.objects.filter(user=user).prefetch_related("cards")
        return Response({
            "ok": True,
            "success": True,
            "decks": [
                {
                    "id": d.id,
                    "title": d.title,
                    "cards": [
                        {"id": c.id, "front": c.front, "back": c.back, "topic": c.topic, "difficulty": c.difficulty}
                        for c in d.cards.all()
                    ],
                }
                for d in decks
            ],
        })

    def post(self, request):
        user, profile, error = require_student(request)
        if error:
            return error
        title = request.data.get("title") or "Saved flashcards"
        cards = request.data.get("cards") or []
        valid_cards = []
        for card in cards[:80]:
            if not isinstance(card, dict):
                continue
            front = str(card.get("front") or "").strip()
            back = str(card.get("back") or "").strip()
            if len(front.split()) < 5 or not front.endswith("?") or not back:
                continue
            valid_cards.append((front[:1000], back[:2000], str(card.get("topic") or "")[:120], str(card.get("difficulty") or "medium")[:20]))
        if not valid_cards:
            return api_error("No valid flashcards were supplied. Each card needs a complete question and answer.", 400)
        source_chat = find_chat(request, request.data.get("chat_id"), user=user, claim_guest=False) if request.data.get("chat_id") else None
        with transaction.atomic():
            deck = FlashcardDeck.objects.create(user=user, title=str(title)[:180], source_chat=source_chat)
            Flashcard.objects.bulk_create([
                Flashcard(deck=deck, front=front, back=back, topic=topic, difficulty=difficulty)
                for front, back, topic, difficulty in valid_cards
            ])
        return Response({"ok": True, "success": True, "deck_id": deck.id, "card_count": len(valid_cards)})


class StudentAccessRequestView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        return Response({"ok": True, "success": True, "message": "Student access requests are handled through the admin approval workflow."})


class StudentPromptConfigView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user, profile, error = require_student(request)
        if error:
            return error
        return Response({"ok": True, "success": True, "prompts": {"answer_agent": answer_agent.ANSWER_SYSTEM_PROMPT}})


@api_view(["GET"])
def view_student_document(request, pk: int):
    user = get_user_from_request(request)
    if not user:
        return Response({"ok": False, "detail": "Sign in first."}, status=401)
    doc = StudentDocument.objects.filter(id=pk, user=user, active=True).first()
    if not doc or not doc.file:
        return Response({"ok": False, "detail": "Document not found."}, status=404)
    return FileResponse(doc.file.open("rb"), filename=safe_title(doc.title), as_attachment=False)


@api_view(["GET"])
def download_student_document(request, pk: int):
    user = get_user_from_request(request)
    if not user:
        return Response({"ok": False, "detail": "Sign in first."}, status=401)
    doc = StudentDocument.objects.filter(id=pk, user=user, active=True).first()
    if not doc or not doc.file:
        return Response({"ok": False, "detail": "Document not found."}, status=404)
    return FileResponse(doc.file.open("rb"), filename=safe_title(doc.title), as_attachment=True)




def _decode_kb_source_token(token: str):
    try:
        data = signing.loads(token)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    uri = data.get("s3_uri") or ""
    if not isinstance(uri, str) or not uri.startswith("s3://"):
        return None
    return data


def _parse_s3_uri(uri: str):
    rest = uri[5:]
    bucket, _, key = rest.partition("/")
    if not bucket or not key:
        return None, None
    return bucket, key


def _serve_kb_s3_object(request, token: str, *, download: bool):
    user = get_user_from_request(request)
    if not user:
        return Response({"ok": False, "detail": "Sign in first."}, status=401)
    profile = getattr(user, "lafre_profile", None)
    if not profile or not profile.can_use_student or not profile.is_active_for_platform():
        return Response({"ok": False, "detail": "Student access required."}, status=403)
    data = _decode_kb_source_token(token)
    if not data:
        return Response({"ok": False, "detail": "Source link is no longer valid."}, status=404)
    bucket, key = _parse_s3_uri(data["s3_uri"])
    if not bucket or not key:
        return Response({"ok": False, "detail": "Source file could not be opened."}, status=404)
    try:
        import boto3
        from django.conf import settings
        region = getattr(settings, "AWS_REGION", "us-east-1")
        s3 = boto3.client("s3", region_name=region)
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read()
        content_type = obj.get("ContentType") or "application/octet-stream"
        filename = safe_title(data.get("title") or Path(key).name)
    except Exception:
        return Response({"ok": False, "detail": "Could not open this knowledge-base document right now."}, status=404)
    response = HttpResponse(body, content_type=content_type)
    disposition = "attachment" if download else "inline"
    response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


@api_view(["GET"])
def view_kb_source_document(request, token: str):
    return _serve_kb_s3_object(request, token, download=False)


@api_view(["GET"])
def download_kb_source_document(request, token: str):
    return _serve_kb_s3_object(request, token, download=True)


@api_view(["GET"])
def get_presigned_url(request):
    return Response({"ok": False, "detail": "Direct storage links are disabled. Use the clean document view/download endpoints."}, status=400)
