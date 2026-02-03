from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import UserProfiles, Teams, TicketTransaction


@admin.register(Teams)
class TeamsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_open", "created_at", "updated_at")
    list_filter = ("is_open",)
    search_fields = ("name",)


@admin.register(UserProfiles)
class UserProfilesAdmin(BaseUserAdmin):
    model = UserProfiles
    ordering = ("id",)
    list_display = ("id", "email", "display_name", "team", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "team")
    search_fields = ("email", "display_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name", "team", "last_recovery_at")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "display_name", "password1", "password2", "is_active", "is_staff"),
        }),
    )

    readonly_fields = ("created_at", "updated_at", "last_login")


@admin.register(TicketTransaction)
class TicketTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "owner_type", "user", "team", "source", "amount", "ref_type", "ref_id", "created_at")
    list_filter = ("owner_type", "source")
    search_fields = ("ref_type", "ref_id")