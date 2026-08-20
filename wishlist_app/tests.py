from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from catalog.models import TCGCard
from catalog.tests import make_catalog

from .models import WishlistItem


class WishlistTests(TestCase):
    def setUp(self):
        self.species, self.tcg_set, self.card = make_catalog()
        self.user = User.objects.create_user("collector", password="safe-password-123")
        self.other = User.objects.create_user("other", password="safe-password-123")

    def test_wishlist_requires_login(self):
        url = reverse("wishlist:list")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_toggle_adds_and_removes_only_current_users_item(self):
        WishlistItem.objects.create(user=self.other, card=self.card)
        self.client.force_login(self.user)
        url = reverse("wishlist:toggle", args=[self.card.slug])

        self.assertEqual(self.client.get(url).status_code, 400)
        self.client.post(url)
        self.assertTrue(WishlistItem.objects.filter(user=self.user, card=self.card).exists())
        self.assertTrue(WishlistItem.objects.filter(user=self.other, card=self.card).exists())

        self.client.post(url)
        self.assertFalse(WishlistItem.objects.filter(user=self.user, card=self.card).exists())
        self.assertTrue(WishlistItem.objects.filter(user=self.other, card=self.card).exists())

    def test_duplicate_card_is_rejected_per_user(self):
        WishlistItem.objects.create(user=self.user, card=self.card)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WishlistItem.objects.create(user=self.user, card=self.card)

    def test_htmx_toggle_returns_active_star_and_silent_update_event(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("wishlist:toggle", args=[self.card.slug]),
            {"placement": "detail"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "wishlist-toggle-detail is-active")
        self.assertContains(response, 'aria-pressed="true"')
        self.assertIn("wishlist:updated", response.headers["HX-Trigger"])
        self.assertNotIn("message", response.headers["HX-Trigger"])

    def test_list_summarizes_and_filters_private_items(self):
        WishlistItem.objects.create(user=self.user, card=self.card)
        second = TCGCard.objects.create(
            external_id="other-1", name="Eevee", set=self.tcg_set, number="2"
        )
        WishlistItem.objects.create(user=self.user, card=second)
        WishlistItem.objects.create(user=self.other, card=second)
        self.client.force_login(self.user)

        response = self.client.get(reverse("wishlist:list"), {"q": "Pika"})

        self.assertContains(response, "Pikachu")
        self.assertNotContains(response, "Eevee")
        self.assertEqual(response.context["totals"]["cards"], 2)

    def test_catalog_and_detail_render_star_state(self):
        WishlistItem.objects.create(user=self.user, card=self.card)
        self.client.force_login(self.user)

        species_response = self.client.get(self.species.get_absolute_url())
        detail_response = self.client.get(self.card.get_absolute_url())

        self.assertContains(species_response, "wishlist-toggle-grid is-active")
        self.assertContains(detail_response, "wishlist-toggle-detail is-active")
        self.assertContains(detail_response, reverse("wishlist:toggle", args=[self.card.slug]))
