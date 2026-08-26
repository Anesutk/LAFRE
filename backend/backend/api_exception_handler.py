from __future__ import annotations

import logging
import traceback

from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def lafre_exception_handler(exc, context):
    logger.exception("LAFRE API error: %s", exc)
    response = exception_handler(exc, context)
    if response is not None:
        data = response.data if isinstance(response.data, dict) else {"detail": response.data}
        message = data.get("detail") or data.get("message") or "Request failed."
        response.data = {
            "ok": False,
            "success": False,
            "message": str(message),
            "detail": str(message),
            "errors": data,
        }
        if settings.DEBUG:
            response.data["debug"] = f"{exc.__class__.__name__}: {exc}"
            response.data["traceback"] = traceback.format_exc(limit=8)
        return response

    payload = {
        "ok": False,
        "success": False,
        "message": "The backend hit an internal error.",
        "detail": "The backend hit an internal error.",
        "errors": {"non_field_errors": [str(exc)]},
    }
    if settings.DEBUG:
        payload["debug"] = f"{exc.__class__.__name__}: {exc}"
        payload["traceback"] = traceback.format_exc(limit=12)
    return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
