from django.contrib import admin
from django.urls import path, include
from apps.common.api.health import healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz),

    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.reservations.urls")),   # / をダッシュボードにする
]