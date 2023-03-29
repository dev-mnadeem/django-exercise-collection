from django.urls import path

from interview.core.views import HealthCheckView

app_name = "core"

urlpatterns = [
    path("healthz/", HealthCheckView.as_view(), name="healthz"),
]
