"""The liveness probe the container healthcheck calls."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_healthz_reports_ok(api_client):
    response = api_client.get(reverse("core:healthz"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_healthz_reports_503_when_the_database_is_unreachable(api_client, monkeypatch):
    from interview.core import views

    class _BrokenConnection:
        def cursor(self):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(views, "connection", _BrokenConnection())

    response = api_client.get(reverse("core:healthz"))

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


@pytest.mark.django_db
def test_healthz_needs_no_credentials(api_client):
    """An orchestrator cannot log in, so the probe must stay open."""
    from interview.core.views import HealthCheckView
    from rest_framework.permissions import AllowAny

    assert HealthCheckView.permission_classes == [AllowAny]
