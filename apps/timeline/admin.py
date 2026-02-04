from django.contrib import admin
from .models import TimelinePost, Like

@admin.register(TimelinePost)
class TimelinePostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "team", "reservation", "visibility", "created_at")
    list_filter = ("visibility", "team")
    search_fields = ("user__email", "user__display_name")
    ordering = ("-created_at",)

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "created_at")
    search_fields = ("user__email",)
    ordering = ("-created_at",)
