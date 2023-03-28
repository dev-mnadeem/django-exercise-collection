from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from interview.profiles.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    """Admin for the email-authenticated user model.

    ``UserAdmin``'s stock fieldsets reference a ``username`` credential that
    this model does not authenticate with, so they are redefined around email.
    """

    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("username", "first_name", "last_name", "avatar")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
