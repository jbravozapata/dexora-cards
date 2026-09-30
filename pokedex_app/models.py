from django.conf import settings
from django.db import models


class UserPokemon(models.Model):
    """A species registered in a user's general Pokémon collection."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_pokemon",
    )
    species = models.ForeignKey(
        "catalog.PokemonSpecies",
        on_delete=models.CASCADE,
        related_name="owners",
    )
    obtained_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["species__national_dex_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "species"], name="unique_owned_species_per_user"
            )
        ]
        indexes = [models.Index(fields=["user", "species"])]
        verbose_name = "Pokémon obtenido"
        verbose_name_plural = "Pokémon obtenidos"

    def __str__(self):
        return f"{self.user} · {self.species}"
