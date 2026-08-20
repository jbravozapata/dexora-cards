from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class UserCollectionItem(models.Model):
    class Variant(models.TextChoices):
        STANDARD = "standard", "Estándar"
        REVERSE = "reverse", "Reverse holo"
        HOLO = "holo", "Holo"
        OTHER = "other", "Otra"

    class Condition(models.TextChoices):
        MINT = "mint", "Mint"
        NEAR_MINT = "near_mint", "Near Mint"
        EXCELLENT = "excellent", "Excelente"
        GOOD = "good", "Buena"
        PLAYED = "played", "Jugada"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collection_items")
    card = models.ForeignKey("catalog.TCGCard", on_delete=models.CASCADE, related_name="collection_items")
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    variant = models.CharField(max_length=20, choices=Variant.choices, default=Variant.STANDARD)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEAR_MINT)
    notes = models.TextField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["user", "card", "variant", "condition"], name="unique_collection_card_variant_condition")]
        indexes = [models.Index(fields=["user", "card"])]

    def __str__(self):
        return f"{self.user} · {self.card} × {self.quantity}"
