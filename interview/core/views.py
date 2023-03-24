"""Operational endpoints.

The core app holds shared plumbing rather than a domain; the only thing it
exposes over HTTP is the liveness probe the container healthcheck calls.
"""

from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Report whether the process is up and the database is reachable.

    Always reachable without credentials, including under the production
    settings, because an orchestrator cannot authenticate.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request, *args, **kwargs) -> Response:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:  # noqa: BLE001 - any driver error means "not ready"
            return Response(
                {"status": "unhealthy", "database": "unreachable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "ok", "database": "ok"}, status=status.HTTP_200_OK)
