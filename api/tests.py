from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from catalog.models import PokemonSpecies, TCGCard, TCGSet
from collections_app.models import UserCollectionItem
from pokedex_app.models import UserPokemon
from wishlist_app.models import WishlistItem


class MobileApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(username="mobile", password="Dexora-2026!")
        cls.other = user_model.objects.create_user(username="other", password="Dexora-2026!")
        cls.species = [
            PokemonSpecies.objects.create(
                national_dex_number=index,
                api_name=f"pokemon-{index}",
                display_name=f"Pokémon {index}",
                slug=f"{index}-pokemon-{index}",
                generation="Generación I",
                primary_type="normal",
            )
            for index in range(1, 19)
        ]
        cls.tcg_set = TCGSet.objects.create(external_id="mobile-set", name="Mobile Set")
        cls.card = TCGCard.objects.create(
            external_id="mobile-card", name="Pokémon 1", slug="mobile-card", set=cls.tcg_set, number="1"
        )
        cls.card.species.add(cls.species[0])

    def authenticate(self, user=None):
        token, _ = Token.objects.get_or_create(user=user or self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_login_returns_token_without_exposing_password(self):
        response = self.client.post(reverse("api:login"), {
            "username": "mobile", "password": "Dexora-2026!",
        }, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["token"])
        self.assertNotIn("password", response.data)

    def test_api_requires_authentication(self):
        response = self.client.get(reverse("api:my-pokemon"))

        self.assertEqual(response.status_code, 401)

    def test_personal_pokedex_is_fixed_to_sixteen_items_per_page(self):
        self.authenticate()

        first_page = self.client.get(reverse("api:my-pokemon"))
        second_page = self.client.get(reverse("api:my-pokemon"), {"page": 2})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(len(first_page.data["results"]), 16)
        self.assertEqual(len(second_page.data["results"]), 2)
        self.assertEqual(first_page.data["summary"]["page_size"], 16)
        self.assertEqual(first_page.data["summary"]["total"], 18)
        self.assertTrue(all(item["artwork"] for item in first_page.data["results"]))

    def test_toggle_owned_pokemon_is_idempotent_and_private(self):
        self.authenticate()
        url = reverse("api:my-pokemon-toggle", args=[self.species[0].pk])

        added = self.client.post(url, {"owned": True}, format="json")
        repeated = self.client.post(url, {"owned": True}, format="json")

        self.assertEqual(added.status_code, 200)
        self.assertTrue(repeated.data["is_owned"])
        self.assertEqual(UserPokemon.objects.filter(user=self.user, species=self.species[0]).count(), 1)
        self.assertFalse(UserPokemon.objects.filter(user=self.other, species=self.species[0]).exists())

        removed = self.client.post(url, {"owned": False}, format="json")
        self.assertFalse(removed.data["is_owned"])
        self.assertFalse(UserPokemon.objects.filter(user=self.user, species=self.species[0]).exists())

    def test_collection_add_increments_only_authenticated_user(self):
        self.authenticate()
        url = reverse("api:collection")

        self.client.post(url, {"card_id": self.card.pk}, format="json")
        response = self.client.post(url, {"card_id": self.card.pk}, format="json")

        item = UserCollectionItem.objects.get(user=self.user, card=self.card)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(item.quantity, 2)
        self.assertFalse(UserCollectionItem.objects.filter(user=self.other).exists())

    def test_wishlist_toggle_does_not_affect_another_user(self):
        WishlistItem.objects.create(user=self.other, card=self.card)
        self.authenticate()
        url = reverse("api:wishlist-toggle")

        added = self.client.post(url, {"card_id": self.card.pk}, format="json")
        removed = self.client.post(url, {"card_id": self.card.pk}, format="json")

        self.assertTrue(added.data["is_wished"])
        self.assertFalse(removed.data["is_wished"])
        self.assertTrue(WishlistItem.objects.filter(user=self.other, card=self.card).exists())
