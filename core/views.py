from django.core.cache import cache
from django.db.models import Count
from django.shortcuts import render

from catalog.models import PokemonSpecies, TCGCard
from .selectors import collection_home_stats


def home(request):
    stats = cache.get("catalog-home-stats")
    if stats is None:
        stats = {
            "species": PokemonSpecies.objects.filter(is_active=True).count(),
            "cards": TCGCard.objects.filter(is_visible=True).count(),
        }
        cache.set("catalog-home-stats", stats, 300)
    carousel_species = (
        PokemonSpecies.objects.filter(is_active=True)
        .annotate(card_count=Count("cards", distinct=True))
        .order_by("national_dex_number")
    )
    featured_cards = TCGCard.objects.filter(is_visible=True).select_related("set").order_by("-updated_at")[:4]
    return render(
        request,
        "core/home.html",
        {
            "stats": stats,
            "collection_stats": collection_home_stats(request.user),
            "carousel_species": carousel_species,
            "carousel_duration": max(stats["species"] * 2, 50),
            "featured_cards": featured_cards,
        },
    )
