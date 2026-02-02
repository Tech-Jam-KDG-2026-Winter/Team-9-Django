from django.contrib import admin
from django.urls import path, include
from apps.common.api.health import healthz
from apps.reservations import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz),

    path("", views.dashboard, name="dashboard"),
    path("auth/", include("apps.accounts.urls")),
    path("reservations/", include("apps.reservations.urls")),
    path("timeline/", include("apps.timeline.urls")),
]