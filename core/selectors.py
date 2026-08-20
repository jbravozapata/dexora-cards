from django.db.models import Count, Sum

from catalog.models import PokemonSpecies
from collections_app.models import UserCollectionItem


def collection_home_stats(user):
    """Return ownership metrics for the signed-in collector."""
    if not user.is_authenticated:
        return {
            "pokemon": 0,
            "cards": 0,
            "top_generation": "—",
        }

    items = UserCollectionItem.objects.filter(user=user)
    totals = items.aggregate(cards=Sum("quantity"))
    pokemon = (
        PokemonSpecies.objects.filter(cards__collection_items__user=user)
        .distinct()
        .count()
    )
    leading_generation = (
        items.exclude(card__species__generation="")
        .values("card__species__generation")
        .annotate(cards=Sum("quantity"), pokemon=Count("card__species", distinct=True))
        .order_by("-cards", "-pokemon", "card__species__generation")
        .first()
    )
    return {
        "pokemon": pokemon,
        "cards": totals["cards"] or 0,
        "top_generation": (
            leading_generation["card__species__generation"]
            if leading_generation
            else "—"
        ),
    }
