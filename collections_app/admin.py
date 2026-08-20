from django.contrib import admin
from .models import UserCollectionItem


@admin.register(UserCollectionItem)
class UserCollectionItemAdmin(admin.ModelAdmin):
    list_display = ("user", "card", "quantity", "variant", "condition", "updated_at")
    list_filter = ("variant", "condition", "updated_at")
    search_fields = ("user__username", "user__email", "card__name", "card__external_id")
    autocomplete_fields = ("user", "card")
    readonly_fields = ("created_at", "updated_at")
