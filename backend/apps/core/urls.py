from django.urls import path

from .views import HealthCheckView

urlpatterns = [
    # GET /api/health/ -> {"status": "ok", "database": "ok"}
    path("health/", HealthCheckView.as_view(), name="health"),
]
