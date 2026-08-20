from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CardImageForm
from .models import PokemonSpecies, TCGCard, TCGSet
from .selectors import (
    available_generations,
    card_version_neighbors,
    cards_for_species,
    filtered_species,
    species_neighbors,
    tcg_coverage_for_species,
)


def species_list(request):
    species_qs = filtered_species(request.GET)
    page = Paginator(species_qs, 24).get_page(request.GET.get("page"))
    context = {
        "page_obj": page,
        "generations": available_generations(),
        "types": sorted(set(PokemonSpecies.objects.exclude(primary_type="").values_list("primary_type", flat=True)) | set(PokemonSpecies.objects.exclude(secondary_type="").values_list("secondary_type", flat=True))),
    }
    template = "catalog/partials/species_results.html" if request.headers.get("HX-Request") else "catalog/species_list.html"
    return render(request, template, context)


def species_detail(request, slug):
    species = get_object_or_404(PokemonSpecies, slug=slug, is_active=True)
    previous_species, next_species, species_total = species_neighbors(species)
    base = TCGCard.objects.filter(is_visible=True, species=species)
    page = Paginator(cards_for_species(species, request.GET), 20).get_page(request.GET.get("page"))
    wishlist_card_ids = set()
    if request.user.is_authenticated:
        wishlist_card_ids = set(request.user.wishlist_items.filter(
            card_id__in=[card.pk for card in page.object_list]
        ).values_list("card_id", flat=True))
    for card in page.object_list:
        card.is_wished = card.pk in wishlist_card_ids
        card.quick_owned_quantity = 0
    if request.user.is_authenticated:
        owned = {
            item.card_id: item.quantity
            for item in request.user.collection_items.filter(
                card_id__in=[card.pk for card in page.object_list],
                variant="standard",
                condition="near_mint",
            )
        }
        for card in page.object_list:
            card.quick_owned_quantity = owned.get(card.pk, 0)
    context = {
        "species": species,
        "page_obj": page,
        "sets": TCGSet.objects.filter(cards__species=species, cards__is_visible=True).distinct().order_by("-release_date"),
        "rarities": base.exclude(rarity="").values_list("rarity", flat=True).distinct().order_by("rarity"),
        "years": base.exclude(set__release_date=None).values_list("set__release_date__year", flat=True).distinct().order_by("-set__release_date__year"),
        "total_cards": base.count(),
        "previous_species": previous_species,
        "next_species": next_species,
        "species_total": species_total,
        "wishlist_card_ids": wishlist_card_ids,
        "tcg_coverage": tcg_coverage_for_species(species),
    }
    template = "catalog/partials/card_results.html" if request.headers.get("HX-Request") else "catalog/species_detail.html"
    return render(request, template, context)


def card_detail(request, slug):
    card = get_object_or_404(TCGCard.objects.select_related("set").prefetch_related("species"), slug=slug, is_visible=True)
    navigation_species, previous_card, next_card, card_position, version_count = card_version_neighbors(card)
    item = None
    if request.user.is_authenticated:
        item = card.collection_items.filter(user=request.user).first()
    is_wished = request.user.is_authenticated and card.wishlist_items.filter(user=request.user).exists()
    return render(request, "catalog/card_detail.html", {
        "card": card,
        "collection_item": item,
        "navigation_species": navigation_species,
        "previous_card": previous_card,
        "next_card": next_card,
        "card_position": card_position,
        "version_count": version_count,
        "is_wished": is_wished,
    })


@staff_member_required
def card_image_upload(request, slug):
    card = get_object_or_404(TCGCard, slug=slug)
    if request.method == "POST":
        form = CardImageForm(request.POST, request.FILES, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, "Imagen personalizada actualizada.")
            return redirect(card)
    else:
        form = CardImageForm(instance=card)
    return render(request, "catalog/card_image_form.html", {"form": form, "card": card})
