from __future__ import annotations

from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


def api_root(request):
    return JsonResponse({
        "ok": True,
        "service": "LAFRE backend",
        "api": "ready",
        "endpoints": {
            "accounts": "/api/accounts/",
            "students": "/api/students/",
            "civilian": "/api/civilian/",
            "health": "/api/health/",
        },
    })


def health(request):
    return JsonResponse({
        "ok": True,
        "service": "LAFRE backend",
        "status": "running",
        "time": timezone.now().isoformat(),
    })


def database_health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({
            "ok": True,
            "service": "LAFRE backend",
            "database": "connected",
            "engine": connection.vendor,
            "time": timezone.now().isoformat(),
        })
    except Exception as exc:
        return JsonResponse({
            "ok": False,
            "service": "LAFRE backend",
            "database": "unavailable",
            "error": str(exc)[:300],
            "time": timezone.now().isoformat(),
        }, status=503)
