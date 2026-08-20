from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalog.tests import make_catalog
from collections_app.models import UserCollectionItem


class HomeTests(TestCase):
    def test_home_works(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="hero-atmosphere"')
        self.assertContains(response, 'aria-hidden="true"')

    def test_home_shows_personal_collection_stats(self):
        species, _, card = make_catalog()
        user = User.objects.create_user("home-collector", password="safe-password-123")
        UserCollectionItem.objects.create(user=user, card=card, quantity=3)
        self.client.force_login(user)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.context["collection_stats"]["pokemon"], 1)
        self.assertEqual(response.context["collection_stats"]["cards"], 3)
        self.assertEqual(
            response.context["collection_stats"]["top_generation"],
            species.generation,
        )
        self.assertEqual(response.context["carousel_species"].count(), 1)
        self.assertContains(response, 'class="species-carousel"')
