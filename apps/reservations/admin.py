from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "team", "start_at", "status", "used_recovery")
    list_filter = ("status", "used_recovery", "team")
    search_fields = ("user__email", "user__display_name")
    ordering = ("-start_at",)