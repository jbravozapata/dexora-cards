from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from PIL import Image, UnidentifiedImageError

from catalog.models import PokemonSpecies, TCGCard

from .models import UserProfile
from .widgets import DexoraImageInput


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ""

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            "avatar", "cover_image", "display_name", "collector_title", "motto", "bio",
            "location", "collecting_since", "favorite_species", "favorite_type",
            "featured_card", "accent",
        )
        widgets = {
            "avatar": DexoraImageInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "cover_image": DexoraImageInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Cuenta brevemente qué te gusta coleccionar."}),
            "motto": forms.TextInput(attrs={"placeholder": "Una frase corta que te represente"}),
            "location": forms.TextInput(attrs={"placeholder": "Ciudad o país (opcional)"}),
            "collecting_since": forms.NumberInput(attrs={"min": 1996}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["favorite_species"].queryset = PokemonSpecies.objects.filter(is_active=True).order_by("national_dex_number")
        self.fields["favorite_species"].empty_label = "Sin seleccionar"
        self.fields["featured_card"].queryset = (
            TCGCard.objects.filter(is_visible=True, collection_items__user=user)
            .select_related("set").distinct().order_by("name", "set__name")
        )
        self.fields["featured_card"].empty_label = "Sin carta destacada"
        self.fields["avatar"].help_text = "JPG, PNG o WebP. Máximo 4 MB."
        self.fields["avatar"].error_messages["invalid_image"] = "Sube una imagen válida en JPG, PNG o WebP."
        self.fields["cover_image"].help_text = "JPG, PNG o WebP. Recomendado 1600 × 500 px; máximo 6 MB."
        self.fields["cover_image"].error_messages["invalid_image"] = "Sube una portada válida en JPG, PNG o WebP."
        self.fields["collecting_since"].min_value = 1996
        self.fields["collecting_since"].max_value = date.today().year
        self.fields["collecting_since"].widget.attrs.update({"min": 1996, "max": date.today().year})

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar or not hasattr(avatar, "file"):
            return avatar
        try:
            image = Image.open(avatar)
            image.verify()
            avatar.seek(0)
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("Sube una imagen válida en JPG, PNG o WebP.")
        return avatar

    def clean_cover_image(self):
        cover = self.cleaned_data.get("cover_image")
        if not cover or not hasattr(cover, "file"):
            return cover
        try:
            image = Image.open(cover)
            image.verify()
            cover.seek(0)
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("Sube una portada válida en JPG, PNG o WebP.")
        return cover

    def clean_featured_card(self):
        card = self.cleaned_data.get("featured_card")
        if card and not self.user.collection_items.filter(card=card).exists():
            raise forms.ValidationError("Solo puedes destacar una carta de tu colección.")
        return card
