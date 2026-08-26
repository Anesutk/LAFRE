import uuid
from django.utils.deprecation import MiddlewareMixin

class SessionIdMiddleware(MiddlewareMixin):
    """
    Ensures every request has an X-Session-ID header.
    If not present, generates one and adds it to request.META.
    """
    def process_request(self, request):
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            session_id = str(uuid.uuid4())
            # Set it so views can access it
            request.META["HTTP_X_SESSION_ID"] = session_id