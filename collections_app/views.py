from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from catalog.models import PokemonSpecies, TCGCard
from .forms import CollectionItemForm
from .models import UserCollectionItem


def _add_default_copy(user, card):
    with transaction.atomic():
        item, created = UserCollectionItem.objects.select_for_update().get_or_create(
            user=user,
            card=card,
            variant=UserCollectionItem.Variant.STANDARD,
            condition=UserCollectionItem.Condition.NEAR_MINT,
            defaults={"quantity": 1},
        )
        if not created:
            item.quantity += 1
            item.save(update_fields=["quantity", "updated_at"])
    return item


@login_required
def collection_list(request):
    items = UserCollectionItem.objects.filter(user=request.user).select_related("card", "card__set").prefetch_related("card__species")
    query = request.GET.get("q", "").strip()
    if query:
        items = items.filter(Q(card__name__icontains=query) | Q(card__set__name__icontains=query))
    if request.GET.get("set"):
        items = items.filter(card__set__external_id=request.GET["set"])
    totals = UserCollectionItem.objects.filter(user=request.user).aggregate(different=Count("card", distinct=True), copies=Sum("quantity"))
    species_owned = UserCollectionItem.objects.filter(user=request.user, card__species__isnull=False).values("card__species").distinct().count()
    page = Paginator(items, 20).get_page(request.GET.get("page"))
    wishlist_card_ids = set(request.user.wishlist_items.filter(
        card_id__in=[item.card_id for item in page.object_list]
    ).values_list("card_id", flat=True))
    for item in page.object_list:
        item.card.is_wished = item.card_id in wishlist_card_ids
    sets = UserCollectionItem.objects.filter(user=request.user).values("card__set__external_id", "card__set__name").distinct().order_by("card__set__name")
    return render(request, "collections/collection_list.html", {"page_obj": page, "totals": totals, "species_owned": species_owned, "sets": sets, "wishlist_card_ids": wishlist_card_ids})


@login_required
def item_edit(request, card_slug):
    card = get_object_or_404(TCGCard, slug=card_slug, is_visible=True)
    item = UserCollectionItem.objects.filter(user=request.user, card=card).first()
    if request.method == "POST":
        form = CollectionItemForm(request.POST, instance=item)
        if form.is_valid():
            entry = form.save(commit=False); entry.user = request.user; entry.card = card; entry.save()
            return redirect(card)
    else:
        form = CollectionItemForm(instance=item)
    return render(request, "collections/item_form.html", {"form": form, "card": card, "item": item})


@login_required
def item_delete(request, pk):
    item = get_object_or_404(UserCollectionItem, pk=pk, user=request.user)
    if request.method == "POST":
        item.delete(); messages.success(request, "La carta fue retirada de tu colección.")
        return redirect("collection:list")
    return render(request, "collections/item_confirm_delete.html", {"item": item})


def _quick_picker_context(user, species, added_card=None):
    cards = list(
        TCGCard.objects.filter(species=species, is_visible=True)
        .select_related("set")
        .order_by("-set__release_date", "name", "number")[:24]
    )
    owned = {
        item.card_id: item.quantity
        for item in UserCollectionItem.objects.filter(
            user=user,
            card_id__in=[card.pk for card in cards],
            variant=UserCollectionItem.Variant.STANDARD,
            condition=UserCollectionItem.Condition.NEAR_MINT,
        )
    }
    for card in cards:
        card.quick_owned_quantity = owned.get(card.pk, 0)
    wishlist_card_ids = set(user.wishlist_items.filter(
        card_id__in=[card.pk for card in cards]
    ).values_list("card_id", flat=True))
    for card in cards:
        card.is_wished = card.pk in wishlist_card_ids
    return {
        "species": species,
        "cards": cards,
        "total_cards": TCGCard.objects.filter(species=species, is_visible=True).count(),
        "added_card": added_card,
        "wishlist_card_ids": wishlist_card_ids,
    }


@login_required
def quick_picker(request, species_slug):
    species = get_object_or_404(PokemonSpecies, slug=species_slug, is_active=True)
    return render(request, "collections/partials/quick_picker.html", _quick_picker_context(request.user, species))


@login_required
def quick_add(request, species_slug, card_slug):
    if request.method != "POST":
        return HttpResponseBadRequest("Esta operacion requiere POST.")
    species = get_object_or_404(PokemonSpecies, slug=species_slug, is_active=True)
    card = get_object_or_404(TCGCard, slug=card_slug, species=species, is_visible=True)
    _add_default_copy(request.user, card)
    context = _quick_picker_context(request.user, species, added_card=card)
    return render(request, "collections/partials/quick_picker.html", context)


@login_required
def card_quick_add(request, card_slug):
    if request.method != "POST":
        return HttpResponseBadRequest("Esta operación requiere POST.")
    card = get_object_or_404(TCGCard, slug=card_slug, is_visible=True)
    item = _add_default_copy(request.user, card)
    if request.headers.get("HX-Request"):
        return render(request, "collections/partials/card_quick_add_button.html", {
            "card": card,
            "owned_quantity": item.quantity,
            "placement": request.POST.get("placement", "grid"),
        })
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect(card)
