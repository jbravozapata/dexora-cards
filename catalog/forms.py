from django import forms
from .models import PokemonSpecies, TCGCard


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class SpeciesArtworkForm(forms.ModelForm):
    class Meta:
        model = PokemonSpecies
        fields = "__all__"

    def clean_custom_artwork(self):
        image = self.cleaned_data.get("custom_artwork")
        if image and getattr(image, "content_type", "") not in ALLOWED_IMAGE_TYPES:
            raise forms.ValidationError("Usa una imagen JPG, PNG o WebP.")
        return image


class CardImageForm(forms.ModelForm):
    class Meta:
        model = TCGCard
        fields = ["custom_image"]

    def clean_custom_image(self):
        image = self.cleaned_data.get("custom_image")
        if image and getattr(image, "content_type", "") not in ALLOWED_IMAGE_TYPES:
            raise forms.ValidationError("Usa una imagen JPG, PNG o WebP.")
        return image
