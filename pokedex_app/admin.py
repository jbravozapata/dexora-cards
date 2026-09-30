from django.contrib import admin

from .models import UserPokemon


@admin.register(UserPokemon)
class UserPokemonAdmin(admin.ModelAdmin):
    list_display = ("user", "species", "obtained_at")
    list_filter = ("species__generation", "obtained_at")
    search_fields = ("user__username", "species__display_name", "species__api_name")
    autocomplete_fields = ("user", "species")
    readonly_fields = ("obtained_at", "updated_at")
