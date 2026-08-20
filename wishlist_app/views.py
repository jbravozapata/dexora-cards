import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from catalog.models import TCGCard

from .models import WishlistItem
from .selectors import filtered_wishlist


@login_required
def wishlist_list(request):
    items = filtered_wishlist(request.user, request.GET)
    totals = WishlistItem.objects.filter(user=request.user, card__is_visible=True).aggregate(
        cards=Count("card", distinct=True),
        species=Count("card__species", distinct=True),
        sets=Count("card__set", distinct=True),
    )
    page = Paginator(items, 20).get_page(request.GET.get("page"))
    sets = (
        WishlistItem.objects.filter(user=request.user, card__is_visible=True)
        .values("card__set__external_id", "card__set__name")
        .distinct()
        .order_by("card__set__name")
    )
    return render(request, "wishlist/wishlist_list.html", {"page_obj": page, "totals": totals, "sets": sets})


@login_required
def toggle_item(request, card_slug):
    if request.method != "POST":
        return HttpResponseBadRequest("Esta operación requiere POST.")
    card = get_object_or_404(TCGCard, slug=card_slug, is_visible=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, card=card)
    if created:
        is_wished = True
    else:
        item.delete()
        is_wished = False

    if request.headers.get("HX-Request"):
        totals = WishlistItem.objects.filter(user=request.user, card__is_visible=True).aggregate(
            cards=Count("card", distinct=True),
            species=Count("card__species", distinct=True),
            sets=Count("card__set", distinct=True),
        )
        placement = request.POST.get("placement", "grid")
        response = render(request, "wishlist/partials/toggle_button.html", {
            "card": card,
            "is_wished": is_wished,
            "placement": placement,
        })
        response["HX-Trigger"] = json.dumps({"wishlist:updated": {
            "active": is_wished,
            "placement": placement,
            "stats": totals,
        }})
        return response

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect(card)
