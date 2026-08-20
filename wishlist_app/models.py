from django.conf import settings
from django.db import models


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    card = models.ForeignKey("catalog.TCGCard", on_delete=models.CASCADE, related_name="wishlist_items")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "card"], name="unique_wishlist_card_per_user")]
        indexes = [models.Index(fields=["user", "card"])]

    def __str__(self):
        return f"{self.user} · {self.card}"
