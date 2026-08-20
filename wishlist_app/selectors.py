from django.db.models import Q

from .models import WishlistItem


def filtered_wishlist(user, params):
    items = (
        WishlistItem.objects.filter(user=user, card__is_visible=True)
        .select_related("card", "card__set")
        .prefetch_related("card__species")
    )
    query = params.get("q", "").strip()
    if query:
        items = items.filter(Q(card__name__icontains=query) | Q(card__set__name__icontains=query))
    if params.get("set"):
        items = items.filter(card__set__external_id=params["set"])
    return items
