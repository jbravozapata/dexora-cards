import re

from django.db.models import Count, Q
from .models import PokemonSpecies, TCGCard


GENERATION_ORDER = (
    "Generación I",
    "Generación II",
    "Generación III",
    "Generación IV",
    "Generación V",
    "Generación VI",
    "Generación VII",
    "Generación VIII",
    "Generación IX",
)

CARD_MECHANIC_SUFFIX = re.compile(
    r"(?:\s+|\s*-\s*)(?:ex|gx|v|vmax|vstar|break|lv\.?\s*x|star)\s*$",
    re.IGNORECASE,
)


def available_generations():
    """Return available generations in National Pokédex order."""
    available = set(
        PokemonSpecies.objects.exclude(generation="").values_list(
            "generation", flat=True
        )
    )
    known = [generation for generation in GENERATION_ORDER if generation in available]
    return known + sorted(available.difference(GENERATION_ORDER))


def filtered_species(params):
    qs = PokemonSpecies.objects.filter(is_active=True).annotate(card_count=Count("cards", filter=Q(cards__is_visible=True), distinct=True))
    query = params.get("q", "").strip()
    if query:
        numeric = query.lstrip("#")
        condition = Q(display_name__icontains=query) | Q(api_name__icontains=query)
        if numeric.isdigit():
            condition |= Q(national_dex_number=int(numeric))
        qs = qs.filter(condition)
    if params.get("generation"):
        qs = qs.filter(generation=params["generation"])
    if params.get("type"):
        qs = qs.filter(Q(primary_type=params["type"]) | Q(secondary_type=params["type"]))
    return qs.order_by("national_dex_number")


def cards_for_species(species, params):
    qs = TCGCard.objects.filter(is_visible=True, species=species).select_related("set").prefetch_related("species")
    if params.get("set"):
        qs = qs.filter(set__external_id=params["set"])
    if params.get("rarity"):
        qs = qs.filter(rarity=params["rarity"])
    if params.get("year", "").isdigit():
        qs = qs.filter(set__release_date__year=int(params["year"]))
    ordering = {"oldest": "set__release_date", "name": "name", "newest": "-set__release_date"}
    return qs.order_by(ordering.get(params.get("order"), "-set__release_date"), "name", "number")


def tcg_coverage_for_species(species):
    """Summarize every printed TCG identity and type linked to one species."""
    rows = TCGCard.objects.filter(is_visible=True, species=species).values_list("name", "types")
    identities = set()
    types = set()
    for name, card_types in rows:
        identity = (name or "").strip()
        while CARD_MECHANIC_SUFFIX.search(identity):
            identity = CARD_MECHANIC_SUFFIX.sub("", identity).strip()
        if identity:
            identities.add(identity)
        types.update(card_type for card_type in (card_types or []) if card_type)
    ordered_identities = sorted(identities, key=str.casefold)
    return {
        "types": sorted(types, key=str.casefold),
        "identities": ordered_identities[:8],
        "identity_count": len(ordered_identities),
        "remaining_identities": max(len(ordered_identities) - 8, 0),
    }


def species_neighbors(species):
    active = PokemonSpecies.objects.filter(is_active=True)
    previous_species = active.filter(
        national_dex_number__lt=species.national_dex_number
    ).order_by("-national_dex_number").first()
    next_species = active.filter(
        national_dex_number__gt=species.national_dex_number
    ).order_by("national_dex_number").first()
    return previous_species, next_species, active.count()


def card_version_neighbors(card):
    navigation_species = card.species.order_by("national_dex_number").first()
    if navigation_species is None:
        return None, None, None, 0, 0
    versions = list(
        TCGCard.objects.filter(is_visible=True, species=navigation_species)
        .order_by("-set__release_date", "name", "number", "external_id")
        .values("external_id", "slug", "name", "set__name")
    )
    try:
        index = next(
            index for index, version in enumerate(versions)
            if version["external_id"] == card.external_id
        )
    except StopIteration:
        return navigation_species, None, None, 0, len(versions)
    previous_card = versions[index - 1] if index > 0 else None
    next_card = versions[index + 1] if index + 1 < len(versions) else None
    return navigation_species, previous_card, next_card, index + 1, len(versions)
