from django.contrib import admin
from django.utils.html import format_html
from .forms import SpeciesArtworkForm
from .models import PokemonSpecies, TCGCard, TCGSet


@admin.register(PokemonSpecies)
class PokemonSpeciesAdmin(admin.ModelAdmin):
    form = SpeciesArtworkForm
    list_display = ("artwork_thumbnail", "national_dex_number", "display_name", "generation", "primary_type", "is_active")
    list_filter = ("generation", "primary_type", "is_active")
    search_fields = ("display_name", "api_name", "=national_dex_number")
    readonly_fields = ("api_name", "external_url", "remote_artwork_url", "artwork_preview", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("display_name",)}

    @admin.display(description="Imagen")
    def artwork_thumbnail(self, obj):
        return format_html('<img src="{}" alt="" style="width:48px;height:48px;object-fit:contain">', obj.effective_artwork)

    @admin.display(description="Vista previa")
    def artwork_preview(self, obj):
        return format_html('<img src="{}" alt="" style="width:220px;height:220px;object-fit:contain">', obj.effective_artwork)


@admin.register(TCGSet)
class TCGSetAdmin(admin.ModelAdmin):
    list_display = ("name", "series", "release_date", "total")
    list_filter = ("series", "release_date")
    search_fields = ("name", "external_id")
    readonly_fields = ("external_id", "created_at", "updated_at")


@admin.action(description="Mostrar cartas seleccionadas")
def make_visible(modeladmin, request, queryset):
    queryset.update(is_visible=True)


@admin.action(description="Ocultar cartas seleccionadas")
def make_hidden(modeladmin, request, queryset):
    queryset.update(is_visible=False)


@admin.register(TCGCard)
class TCGCardAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "set", "number", "rarity", "is_visible", "image_source")
    list_filter = ("is_visible", "image_source", "rarity", "set__series")
    search_fields = ("name", "external_id", "number", "artist")
    filter_horizontal = ("species",)
    readonly_fields = ("external_id", "remote_image_small", "remote_image_large", "created_at", "updated_at", "large_preview")
    actions = (make_visible, make_hidden)

    @admin.display(description="Imagen")
    def thumbnail(self, obj):
        return format_html('<img src="{}" alt="" style="width:42px;height:59px;object-fit:cover;border-radius:4px">', obj.effective_image)

    @admin.display(description="Vista previa")
    def large_preview(self, obj):
        return format_html('<img src="{}" alt="" style="width:180px;border-radius:10px">', obj.effective_image)
