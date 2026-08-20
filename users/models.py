from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


def validate_profile_image_size(file):
    if file.size > 4 * 1024 * 1024:
        raise ValidationError("La imagen no puede superar 4 MB.")


def validate_cover_image_size(file):
    if file.size > 6 * 1024 * 1024:
        raise ValidationError("La portada no puede superar 6 MB.")


class UserProfile(models.Model):
    class CollectorTitle(models.TextChoices):
        COLLECTOR = "collector", "Coleccionista"
        ARCHIVIST = "archivist", "Archivista TCG"
        ILLUSTRATION = "illustration", "Cazador de ilustraciones"
        COMPLETIONIST = "completionist", "Completista"
        EXPLORER = "explorer", "Explorador Cardex"

    class Accent(models.TextChoices):
        CYAN = "cyan", "Cian Dexora"
        GOLD = "gold", "Dorado"
        VIOLET = "violet", "Violeta"
        GREEN = "green", "Verde"
        BLUE = "blue", "Azul"

    TYPE_CHOICES = (
        ("normal", "Normal"), ("fire", "Fuego"), ("water", "Agua"),
        ("electric", "Eléctrico"), ("grass", "Planta"), ("ice", "Hielo"),
        ("fighting", "Lucha"), ("poison", "Veneno"), ("ground", "Tierra"),
        ("flying", "Volador"), ("psychic", "Psíquico"), ("bug", "Bicho"),
        ("rock", "Roca"), ("ghost", "Fantasma"), ("dragon", "Dragón"),
        ("dark", "Siniestro"), ("steel", "Acero"), ("fairy", "Hada"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collector_profile")
    display_name = models.CharField(max_length=60, blank=True)
    collector_title = models.CharField(max_length=24, choices=CollectorTitle.choices, default=CollectorTitle.COLLECTOR)
    motto = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=80, blank=True)
    collecting_since = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1996), MaxValueValidator(date.today().year)],
    )
    favorite_type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True)
    favorite_species = models.ForeignKey("catalog.PokemonSpecies", null=True, blank=True, on_delete=models.SET_NULL, related_name="favorite_of_profiles")
    featured_card = models.ForeignKey("catalog.TCGCard", null=True, blank=True, on_delete=models.SET_NULL, related_name="featured_in_profiles")
    avatar = models.ImageField(
        upload_to="profiles/avatars/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_profile_image_size],
    )
    cover_image = models.ImageField(
        upload_to="profiles/covers/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_cover_image_size],
    )
    accent = models.CharField(max_length=12, choices=Accent.choices, default=Accent.CYAN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil de coleccionista"
        verbose_name_plural = "perfiles de coleccionista"

    def __str__(self):
        return f"Perfil de {self.user.username}"

    @property
    def name(self):
        return self.display_name.strip() or self.user.username

    @property
    def initials(self):
        parts = self.name.split()
        return "".join(part[0] for part in parts[:2]).upper()
