from django.shortcuts import render, redirect
from django.http import JsonResponse
import logging
import datetime

logger = logging.getLogger(__name__)


def index_view(request):
    return render(request, 'index.html')


def health_check(request):
    """
    Simple health-check endpoint used by Render to confirm the service is up.
    Also verifies database connectivity.
    Returns HTTP 200 with JSON so Render's health checker accepts it.
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({'status': 'ok', 'db': db_ok})