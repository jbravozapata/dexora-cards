from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from catalog.models import TCGCard
from catalog.tests import make_catalog
from .models import UserCollectionItem


class CollectionTests(TestCase):
    def setUp(self):
        self.species, self.tcg_set, self.card = make_catalog()
        self.user = User.objects.create_user("collector", password="safe-password-123")
        self.other = User.objects.create_user("other", password="safe-password-123")

    def test_collection_requires_login(self):
        response = self.client.get(reverse("collection:list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('collection:list')}")

    def test_add_update_and_delete_item(self):
        self.client.force_login(self.user)
        url = reverse("collection:item-edit", args=[self.card.slug])
        response = self.client.post(
            url,
            {"quantity": 2, "variant": "standard", "condition": "near_mint", "notes": "Mi copia"},
            follow=True,
        )
        self.assertRedirects(response, self.card.get_absolute_url())
        self.assertNotContains(response, "Tu colecci\u00f3n fue actualizada.")
        item = UserCollectionItem.objects.get(); self.assertEqual(item.quantity, 2)
        self.client.post(url, {"quantity": 4, "variant": "standard", "condition": "near_mint", "notes": ""})
        item.refresh_from_db(); self.assertEqual(item.quantity, 4)
        self.client.post(reverse("collection:item-delete", args=[item.pk]))
        self.assertFalse(UserCollectionItem.objects.exists())

    def test_duplicate_constraint(self):
        UserCollectionItem.objects.create(user=self.user, card=self.card)
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserCollectionItem.objects.create(user=self.user, card=self.card)

    def test_same_pokemon_accepts_multiple_distinct_cards(self):
        second_card = TCGCard.objects.create(
            external_id="base1-59",
            name="Pikachu alternativo",
            set=self.tcg_set,
            number="59",
        )
        second_card.species.add(self.species)
        UserCollectionItem.objects.create(user=self.user, card=self.card)
        UserCollectionItem.objects.create(user=self.user, card=second_card)
        self.assertEqual(self.user.collection_items.count(), 2)
        self.assertEqual(self.species.cards.count(), 2)

    def test_quick_picker_requires_login_and_lists_species_cards(self):
        picker_url = reverse("collection:quick-picker", args=[self.species.slug])
        self.assertRedirects(self.client.get(picker_url), f"{reverse('login')}?next={picker_url}")

        self.client.force_login(self.user)
        response = self.client.get(picker_url)
        self.assertContains(response, self.card.name)
        self.assertContains(response, "quick-card-add")

    def test_quick_add_creates_then_increments_default_copy(self):
        self.client.force_login(self.user)
        url = reverse("collection:quick-add", args=[self.species.slug, self.card.slug])

        self.assertEqual(self.client.get(url).status_code, 400)
        first = self.client.post(url)
        self.assertEqual(first.status_code, 200)
        item = UserCollectionItem.objects.get(user=self.user, card=self.card)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.variant, UserCollectionItem.Variant.STANDARD)
        self.assertEqual(item.condition, UserCollectionItem.Condition.NEAR_MINT)

        second = self.client.post(url)
        self.assertEqual(second.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.assertContains(second, "2 en tu colecci")

    def test_card_grid_quick_add_updates_button_without_alert(self):
        self.client.force_login(self.user)
        url = reverse("collection:card-quick-add", args=[self.card.slug])

        self.assertEqual(self.client.get(url).status_code, 400)
        first = self.client.post(url, {"placement": "grid"}, HTTP_HX_REQUEST="true")
        second = self.client.post(url, {"placement": "grid"}, HTTP_HX_REQUEST="true")

        item = UserCollectionItem.objects.get(user=self.user, card=self.card)
        self.assertEqual(item.quantity, 2)
        self.assertContains(first, 'class="card-owned-badge"')
        self.assertContains(second, ">2</span>")
        self.assertNotIn("HX-Trigger", second.headers)

    def test_species_card_grid_shows_quick_add_and_owned_quantity(self):
        UserCollectionItem.objects.create(user=self.user, card=self.card, quantity=3)
        self.client.force_login(self.user)

        response = self.client.get(self.species.get_absolute_url())

        self.assertContains(response, reverse("collection:card-quick-add", args=[self.card.slug]))
        self.assertContains(response, 'aria-label="3 en tu colecci')

    def test_user_cannot_delete_someone_elses_item(self):
        item = UserCollectionItem.objects.create(user=self.other, card=self.card)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse("collection:item-delete", args=[item.pk])).status_code, 404)
        self.assertTrue(UserCollectionItem.objects.filter(pk=item.pk).exists())

    def test_collection_shows_bulk_management_controls(self):
        UserCollectionItem.objects.create(user=self.user, card=self.card)
        self.client.force_login(self.user)

        response = self.client.get(reverse("collection:list"))

        self.assertContains(response, "Gestionar colección")
        self.assertContains(response, reverse("collection:bulk-delete"))
        self.assertContains(response, 'name="item_ids"')

    def test_bulk_delete_requires_login_and_post(self):
        item = UserCollectionItem.objects.create(user=self.user, card=self.card)
        url = reverse("collection:bulk-delete")

        response = self.client.post(url, {"item_ids": [item.pk]})
        self.assertRedirects(response, f"{reverse('login')}?next={url}")
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_bulk_delete_previews_then_deletes_only_owned_items(self):
        owned = UserCollectionItem.objects.create(user=self.user, card=self.card, quantity=3)
        second_card = TCGCard.objects.create(
            external_id="bulk-second", name="Raichu", set=self.tcg_set, number="14"
        )
        other_card = TCGCard.objects.create(
            external_id="bulk-foreign", name="Eevee", set=self.tcg_set, number="51"
        )
        second = UserCollectionItem.objects.create(user=self.user, card=second_card, quantity=2)
        foreign = UserCollectionItem.objects.create(user=self.other, card=other_card, quantity=9)
        url = reverse("collection:bulk-delete")
        self.client.force_login(self.user)

        preview = self.client.post(url, {"item_ids": [owned.pk, second.pk, foreign.pk]})
        self.assertEqual(preview.status_code, 200)
        self.assertContains(preview, "Retirar selección")
        self.assertContains(preview, "Pikachu")
        self.assertContains(preview, "Raichu")
        self.assertNotContains(preview, "Eevee")
        self.assertContains(preview, "5 ejemplares")

        result = self.client.post(url, {
            "item_ids": [owned.pk, second.pk, foreign.pk],
            "confirm": "yes",
        })
        self.assertRedirects(result, reverse("collection:list"))
        self.assertFalse(UserCollectionItem.objects.filter(pk__in=[owned.pk, second.pk]).exists())
        self.assertTrue(UserCollectionItem.objects.filter(pk=foreign.pk, user=self.other).exists())

    def test_bulk_delete_rejects_empty_or_invalid_selection(self):
        item = UserCollectionItem.objects.create(user=self.user, card=self.card)
        self.client.force_login(self.user)
        url = reverse("collection:bulk-delete")

        response = self.client.post(url, {"item_ids": ["invalid"], "confirm": "yes"})

        self.assertRedirects(response, reverse("collection:list"))
        self.assertTrue(UserCollectionItem.objects.filter(pk=item.pk).exists())

    def test_collection_summary(self):
        UserCollectionItem.objects.create(user=self.user, card=self.card, quantity=3)
        self.client.force_login(self.user)
        response = self.client.get(reverse("collection:list"))
        self.assertContains(response, "cartas diferentes")
        self.assertContains(response, "3")
        self.assertNotContains(response, "ARCHIVO PERSONAL")
        self.assertNotContains(response, "Una lectura clara de las cartas")
