from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "collector_title", "favorite_species", "accent", "updated_at")
    list_filter = ("collector_title", "accent", "favorite_type")
    search_fields = ("user__username", "user__email", "display_name", "location")
    autocomplete_fields = ("user", "favorite_species", "featured_card")
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "user", "display_name", "collector_title", "motto", "bio", "location",
        "collecting_since", "favorite_species", "favorite_type", "featured_card",
        "avatar", "cover_image", "accent", "created_at", "updated_at",
    )
