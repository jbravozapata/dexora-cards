from pathlib import Path

from django.core.exceptions import ValidationError
from hashlib import sha1

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def validate_image_size(file):
    if file.size > 8 * 1024 * 1024:
        raise ValidationError("La imagen no puede superar 8 MB.")


class PokemonSpecies(models.Model):
    national_dex_number = models.PositiveSmallIntegerField(unique=True, db_index=True)
    api_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=120, unique=True)
    generation = models.CharField(max_length=30, blank=True, db_index=True)
    primary_type = models.CharField(max_length=30, blank=True, db_index=True)
    secondary_type = models.CharField(max_length=30, blank=True, db_index=True)
    description = models.TextField(blank=True)
    remote_artwork_url = models.URLField(blank=True, max_length=500)
    custom_artwork = models.ImageField(
        upload_to="pokemon/custom/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
    )
    is_active = models.BooleanField(default=True, db_index=True)
    external_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["national_dex_number"]
        verbose_name = "especie Pokémon"
        verbose_name_plural = "especies Pokémon"
        indexes = [models.Index(fields=["generation", "primary_type"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.national_dex_number}-{self.api_name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.national_dex_number:04d} {self.display_name}"

    def get_absolute_url(self):
        return reverse("catalog:species-detail", kwargs={"slug": self.slug})

    @property
    def types(self):
        return [x for x in (self.primary_type, self.secondary_type) if x]

    @property
    def effective_artwork(self):
        if self.custom_artwork:
            return self.custom_artwork.url
        return self.remote_artwork_url or "/static/images/dexora-mark.png"

    @property
    def has_artwork(self):
        return bool(self.custom_artwork or self.remote_artwork_url)


class TCGSet(models.Model):
    external_id = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=180, db_index=True)
    series = models.CharField(max_length=180, blank=True, db_index=True)
    printed_total = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    release_date = models.DateField(null=True, blank=True, db_index=True)
    symbol_url = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-release_date", "name"]
        verbose_name = "expansión TCG"
        verbose_name_plural = "expansiones TCG"

    def __str__(self):
        return self.name


class TCGCard(models.Model):
    class ImageSource(models.TextChoices):
        AUTOMATIC = "automatic", "Automática"
        CUSTOM = "custom", "Personalizada"
        PLACEHOLDER = "placeholder", "Placeholder"

    external_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=180, db_index=True)
    slug = models.SlugField(max_length=230, unique=True)
    set = models.ForeignKey(TCGSet, on_delete=models.PROTECT, related_name="cards")
    number = models.CharField(max_length=30, blank=True)
    rarity = models.CharField(max_length=100, blank=True, db_index=True)
    artist = models.CharField(max_length=150, blank=True)
    supertype = models.CharField(max_length=50, blank=True)
    subtypes = models.JSONField(default=list, blank=True)
    types = models.JSONField(default=list, blank=True)
    hp = models.CharField(max_length=20, blank=True)
    remote_image_small = models.URLField(blank=True, max_length=500)
    remote_image_large = models.URLField(blank=True, max_length=500)
    custom_image = models.ImageField(
        upload_to="cards/custom/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
    )
    image_source = models.CharField(max_length=20, choices=ImageSource.choices, default=ImageSource.AUTOMATIC)
    species = models.ManyToManyField(PokemonSpecies, related_name="cards", blank=True)
    is_visible = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-set__release_date", "name", "number"]
        indexes = [models.Index(fields=["is_visible", "rarity"]), models.Index(fields=["name", "number"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            # Some external IDs differ only by punctuation, which ``slugify``
            # removes (for example the special-number cards in a set).  Keep
            # readable URLs while adding a stable suffix from the exact ID.
            base = slugify(f"{self.external_id}-{self.name}")[:220].rstrip("-") or "carta"
            digest = sha1(self.external_id.encode("utf-8")).hexdigest()[:8]
            self.slug = f"{base}-{digest}"
        if self.custom_image:
            self.image_source = self.ImageSource.CUSTOM
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} · {self.set.name} #{self.number}"

    def get_absolute_url(self):
        return reverse("catalog:card-detail", kwargs={"slug": self.slug})

    @property
    def effective_image(self):
        if self.custom_image:
            return self.custom_image.url
        return self.remote_image_large or self.remote_image_small or "/static/images/dexora-mark.png"

    @property
    def has_real_image(self):
        return bool(self.custom_image or self.remote_image_large or self.remote_image_small)
