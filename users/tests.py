from io import BytesIO
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.models import TCGCard
from catalog.tests import make_catalog
from collections_app.models import UserCollectionItem

from .models import UserProfile


class SignupTests(TestCase):
    def test_signup_aside_only_shows_animated_logo(self):
        response = self.client.get(reverse("users:signup"))
        self.assertContains(response, "dexora-mark.png")
        self.assertContains(response, "account-brand-image")
        self.assertContains(response, "account-panel")
        self.assertNotContains(response, "auth-layout")
        self.assertNotContains(response, "EMPIEZA TU COLECCIÓN")
        self.assertNotContains(response, "Una colección con contexto")
        self.assertNotContains(response, "Solo lo esencial para comenzar")
        self.assertNotContains(response, "Su contraseña debe contener al menos")
        self.assertNotContains(response, "150 caracteres como máximo")

    def test_login_uses_centered_account_layout(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "account-panel")
        self.assertContains(response, "dexora-mark.png")
        self.assertNotContains(response, "Continúa donde lo dejaste")
        self.assertNotContains(response, "auth-layout")

    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(reverse("users:signup"), {"username": "newcollector", "email": "user@example.com", "password1": "Strong-pass-964!", "password2": "Strong-pass-964!"})
        self.assertRedirects(response, reverse("collection:list"))
        self.assertTrue(User.objects.filter(username="newcollector").exists())

    def test_profile_requires_login_and_works(self):
        url = reverse("users:profile")
        self.assertEqual(self.client.get(url).status_code, 302)
        user = User.objects.create_user("profileuser", email="private@example.com", password="Strong-pass-964!")
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertContains(response, "profileuser")
        self.assertNotContains(response, "CUENTA DE COLECCIONISTA")
        self.assertNotContains(response, "private@example.com")
        self.assertContains(response, "Personalizar")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_can_be_personalized(self):
        species, _, card = make_catalog()
        user = User.objects.create_user("personal", email="nerea.private@example.com", password="Strong-pass-964!")
        UserCollectionItem.objects.create(user=user, card=card)
        self.client.force_login(user)

        response = self.client.post(reverse("users:profile-edit"), {
            "display_name": "Nerea",
            "collector_title": UserProfile.CollectorTitle.ILLUSTRATION,
            "motto": "Cada ilustración cuenta una historia",
            "bio": "Colecciono artes especiales y primeras generaciones.",
            "location": "Quito, Ecuador",
            "collecting_since": 2012,
            "favorite_species": species.pk,
            "favorite_type": "grass",
            "featured_card": card.pk,
            "accent": UserProfile.Accent.GOLD,
        })

        self.assertRedirects(response, reverse("users:profile"))
        profile = user.collector_profile
        self.assertEqual(profile.display_name, "Nerea")
        self.assertEqual(profile.featured_card, card)
        page = self.client.get(reverse("users:profile"))
        self.assertContains(page, "Cada ilustración cuenta una historia")
        self.assertContains(page, "profile-accent-gold")
        self.assertNotContains(page, user.email)

    def test_featured_card_must_belong_to_current_user(self):
        species, tcg_set, owned_card = make_catalog()
        foreign_card = TCGCard.objects.create(
            external_id="foreign-profile-card",
            name="Carta ajena",
            set=tcg_set,
            number="2",
        )
        foreign_card.species.add(species)
        user = User.objects.create_user("secureprofile", password="Strong-pass-964!")
        UserCollectionItem.objects.create(user=user, card=owned_card)
        self.client.force_login(user)

        response = self.client.post(reverse("users:profile-edit"), {
            "collector_title": UserProfile.CollectorTitle.COLLECTOR,
            "featured_card": foreign_card.pk,
            "accent": UserProfile.Accent.CYAN,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Escoja una opción válida")
        self.assertIsNone(user.collector_profile.featured_card)

    def test_profile_rejects_invalid_avatar_content(self):
        user = User.objects.create_user("avatarprofile", password="Strong-pass-964!")
        self.client.force_login(user)
        fake_image = SimpleUploadedFile("avatar.png", b"esto no es una imagen", content_type="image/png")

        response = self.client.post(reverse("users:profile-edit"), {
            "collector_title": UserProfile.CollectorTitle.COLLECTOR,
            "accent": UserProfile.Accent.CYAN,
            "avatar": fake_image,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sube una imagen válida")
        self.assertFalse(user.collector_profile.avatar)

    def test_profile_accepts_cover_and_uses_custom_picker(self):
        user = User.objects.create_user("coverprofile", password="Strong-pass-964!")
        self.client.force_login(user)
        image_bytes = BytesIO()
        Image.new("RGB", (1200, 400), "#12345a").save(image_bytes, format="PNG")
        cover = SimpleUploadedFile("portada.png", image_bytes.getvalue(), content_type="image/png")

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(reverse("users:profile-edit"), {
                "collector_title": UserProfile.CollectorTitle.COLLECTOR,
                "accent": UserProfile.Accent.BLUE,
                "cover_image": cover,
            })
            self.assertRedirects(response, reverse("users:profile"))
            user.collector_profile.refresh_from_db()
            self.assertTrue(user.collector_profile.cover_image.name.startswith("profiles/covers/"))
            page = self.client.get(reverse("users:profile"))
            self.assertContains(page, "profile-cover-image")

        edit_page = self.client.get(reverse("users:profile-edit"))
        self.assertContains(edit_page, "profile-image-picker")
        self.assertNotContains(edit_page, "Actualmente:")
