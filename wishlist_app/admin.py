from django.contrib import admin

from .models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "card", "created_at")
    list_filter = ("created_at", "card__set")
    search_fields = ("user__username", "user__email", "card__name", "card__external_id")
    autocomplete_fields = ("user", "card")
    readonly_fields = ("created_at", "updated_at")
