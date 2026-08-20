from io import BytesIO
from unittest.mock import patch

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import CardImageForm, SpeciesArtworkForm
from .models import PokemonSpecies, TCGCard, TCGSet
from .services import infer_species_from_card_name, link_unlinked_cards, sync_cards, sync_sets, sync_species


def make_catalog():
    species = PokemonSpecies.objects.create(national_dex_number=25, api_name="pikachu", display_name="Pikachu", generation="Generación I", primary_type="eléctrico")
    tcg_set = TCGSet.objects.create(external_id="base1", name="Base", series="Original")
    card = TCGCard.objects.create(external_id="base1-58", name="Pikachu", set=tcg_set, number="58", rarity="Común")
    card.species.add(species)
    return species, tcg_set, card


class ModelTests(TestCase):
    def test_card_species_relation_and_slugs(self):
        species, _, card = make_catalog()
        self.assertIn(species, card.species.all())
        self.assertIn("pikachu", species.slug)
        self.assertIn("pikachu", card.slug)

    def test_card_slugs_remain_unique_when_external_ids_differ_by_punctuation(self):
        tcg_set = TCGSet.objects.create(external_id="special", name="Special", series="Test")
        first = TCGCard.objects.create(external_id="ex10-?", name="Special Card", set=tcg_set)
        second = TCGCard.objects.create(external_id="ex10", name="Special Card", set=tcg_set)

        self.assertNotEqual(first.slug, second.slug)

    def test_image_priority(self):
        _, _, card = make_catalog()
        self.assertEqual(card.effective_image, "/static/images/dexora-mark.png")
        card.remote_image_small = "https://example.com/small.png"
        card.remote_image_large = "https://example.com/large.png"
        self.assertEqual(card.effective_image, "https://example.com/large.png")
        card.custom_image = "cards/custom/local.png"
        self.assertIn("/media/cards/custom/local.png", card.effective_image)

    def test_species_artwork_priority(self):
        species, _, _ = make_catalog()
        self.assertEqual(species.effective_artwork, "/static/images/dexora-mark.png")
        species.remote_artwork_url = "https://example.com/official.png"
        self.assertEqual(species.effective_artwork, "https://example.com/official.png")
        species.custom_artwork = "pokemon/custom/local.png"
        self.assertIn("/media/pokemon/custom/local.png", species.effective_artwork)


class CatalogViewTests(TestCase):
    def setUp(self):
        self.species, self.tcg_set, self.card = make_catalog()

    def test_search_name_and_number(self):
        for query in ("Pika", "25", "#25"):
            response = self.client.get(reverse("catalog:species-list"), {"q": query})
            self.assertContains(response, "Pikachu")

    def test_filters_and_main_pages(self):
        response = self.client.get(reverse("catalog:species-list"), {"generation": "Generación I", "type": "eléctrico"})
        self.assertContains(response, "Pikachu")
        detail_response = self.client.get(self.species.get_absolute_url())
        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(detail_response, "Pokédex nacional")
        self.assertContains(detail_response, "species-number-block")
        self.assertEqual(self.client.get(self.card.get_absolute_url()).status_code, 200)

    def test_species_detail_has_national_dex_neighbors(self):
        previous_species = PokemonSpecies.objects.create(
            national_dex_number=24,
            api_name="arbok",
            display_name="Arbok",
        )
        next_species = PokemonSpecies.objects.create(
            national_dex_number=26,
            api_name="raichu",
            display_name="Raichu",
        )

        response = self.client.get(self.species.get_absolute_url())

        self.assertEqual(response.context["previous_species"], previous_species)
        self.assertEqual(response.context["next_species"], next_species)
        self.assertContains(response, previous_species.get_absolute_url())
        self.assertContains(response, next_species.get_absolute_url())

    def test_card_detail_navigates_versions_of_the_same_species(self):
        previous_card = TCGCard.objects.create(
            external_id="base1-alpha",
            name="Alpha Pikachu",
            set=self.tcg_set,
            number="1",
        )
        next_card = TCGCard.objects.create(
            external_id="base1-zulu",
            name="Zulu Pikachu",
            set=self.tcg_set,
            number="99",
        )
        previous_card.species.add(self.species)
        next_card.species.add(self.species)
        unrelated_species = PokemonSpecies.objects.create(
            national_dex_number=26,
            api_name="raichu",
            display_name="Raichu",
        )
        unrelated_card = TCGCard.objects.create(
            external_id="base1-unrelated",
            name="Middle card",
            set=self.tcg_set,
        )
        unrelated_card.species.add(unrelated_species)

        response = self.client.get(self.card.get_absolute_url())

        self.assertEqual(response.context["navigation_species"], self.species)
        self.assertEqual(response.context["version_count"], 3)
        self.assertEqual(response.context["card_position"], 2)
        self.assertEqual(response.context["previous_card"]["slug"], previous_card.slug)
        self.assertEqual(response.context["next_card"]["slug"], next_card.slug)
        self.assertNotContains(response, unrelated_card.get_absolute_url())

    def test_species_detail_exposes_all_tcg_forms_and_types(self):
        ogerpon = PokemonSpecies.objects.create(
            national_dex_number=1017,
            api_name="ogerpon",
            display_name="Ogerpon",
            generation="Generación IX",
            primary_type="grass",
        )
        variants = (
            ("ogerpon-grass", "Teal Mask Ogerpon ex", "Grass"),
            ("ogerpon-fire", "Hearthflame Mask Ogerpon ex", "Fire"),
            ("ogerpon-water", "Wellspring Mask Ogerpon ex", "Water"),
            ("ogerpon-fighting", "Cornerstone Mask Ogerpon ex", "Fighting"),
        )
        for external_id, name, card_type in variants:
            card = TCGCard.objects.create(
                external_id=external_id,
                name=name,
                set=self.tcg_set,
                types=[card_type],
            )
            card.species.add(ogerpon)

        response = self.client.get(ogerpon.get_absolute_url())

        self.assertEqual(response.context["total_cards"], 4)
        self.assertEqual(
            response.context["tcg_coverage"]["types"],
            ["Fighting", "Fire", "Grass", "Water"],
        )
        self.assertEqual(response.context["tcg_coverage"]["identity_count"], 4)
        for _, name, card_type in variants:
            self.assertContains(response, name.removesuffix(" ex"))
            self.assertContains(response, card_type)

    def test_htmx_returns_partial(self):
        response = self.client.get(reverse("catalog:species-list"), HTTP_HX_REQUEST="true")
        self.assertNotContains(response, "<!doctype html>")

    def test_catalog_uses_type_colored_card_borders_without_intro(self):
        PokemonSpecies.objects.create(
            national_dex_number=1,
            api_name="bulbasaur",
            display_name="Bulbasaur",
            generation="Generación I",
            primary_type="grass",
            secondary_type="poison",
        )
        response = self.client.get(reverse("catalog:species-list"))
        self.assertNotContains(response, "CATÁLOGO DE ESPECIES")
        self.assertNotContains(response, "Una entrada por especie")
        self.assertContains(
            response,
            "type-primary-grass type-secondary-poison is-dual-type",
        )
        self.assertContains(response, 'class="species-type-pattern primary"')
        self.assertContains(response, 'class="species-type-pattern secondary"')

    def test_generations_use_national_dex_order(self):
        PokemonSpecies.objects.create(
            national_dex_number=906,
            api_name="sprigatito",
            display_name="Sprigatito",
            generation="Generación IX",
        )
        response = self.client.get(reverse("catalog:species-list"))
        generations = list(response.context["generations"])
        self.assertLess(
            generations.index("Generación I"),
            generations.index("Generación IX"),
        )

    def test_image_upload_requires_staff(self):
        self.assertEqual(self.client.get(reverse("catalog:card-image-upload", args=[self.card.slug])).status_code, 302)
        staff = User.objects.create_user("staff", password="safe-password-123", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("catalog:card-image-upload", args=[self.card.slug])).status_code, 200)

    def test_image_form_rejects_wrong_type(self):
        upload = SimpleUploadedFile("bad.jpg", b"not-an-image", content_type="text/plain")
        form = CardImageForm(files={"custom_image": upload}, instance=self.card)
        self.assertFalse(form.is_valid())

        artwork_form = SpeciesArtworkForm(
            files={"custom_artwork": upload}, instance=self.species
        )
        self.assertFalse(artwork_form.is_valid())


class FakeClient:
    def __init__(self, responses): self.responses = responses
    def get(self, path, params=None):
        for key, value in sorted(self.responses.items(), key=lambda item: len(item[0]), reverse=True):
            if path.startswith(key): return value
        raise AssertionError(f"Ruta no preparada: {path}")


class SyncServiceTests(TestCase):
    def test_name_inference_supports_regional_forms_and_mask_variants(self):
        vulpix = PokemonSpecies.objects.create(
            national_dex_number=37, api_name="vulpix", display_name="Vulpix"
        )
        ogerpon = PokemonSpecies.objects.create(
            national_dex_number=1017, api_name="ogerpon", display_name="Ogerpon"
        )
        index = {"vulpix": vulpix, "ogerpon": ogerpon}

        self.assertEqual(infer_species_from_card_name("Alolan Vulpix VSTAR", index), [vulpix])
        self.assertEqual(
            infer_species_from_card_name("Cornerstone Mask Ogerpon ex", index),
            [ogerpon],
        )

    def test_species_sync_is_idempotent(self):
        client = FakeClient({
            "pokemon-species": {"results": [{"name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon-species/25/"}]},
            "pokemon-species/25/": {"id": 25, "name": "pikachu", "names": [{"name": "Pikachu", "language": {"name": "es"}}], "generation": {"name": "generation-i"}, "flavor_text_entries": []},
            "pokemon/pikachu": {
                "types": [{"slot": 1, "type": {"name": "electric"}}],
                "sprites": {"other": {"official-artwork": {"front_default": "https://example.com/pikachu.png"}}},
            },
        })
        first = sync_species(client=client); second = sync_species(client=client)
        self.assertEqual(first["created"], 1); self.assertEqual(second["updated"], 1)
        self.assertEqual(PokemonSpecies.objects.count(), 1)
        self.assertEqual(PokemonSpecies.objects.get().remote_artwork_url, "https://example.com/pikachu.png")

    def test_set_and_card_sync_preserves_custom_image(self):
        species = PokemonSpecies.objects.create(national_dex_number=25, api_name="pikachu", display_name="Pikachu")
        set_payload = {"data": [{"id": "sv1", "name": "Escarlata", "series": "SV", "printedTotal": 1, "total": 1, "releaseDate": "2023/03/31", "images": {}}], "pageSize": 250, "totalCount": 1}
        sync_sets(client=FakeClient({"sets": set_payload}))
        card_payload = {"data": [{"id": "sv1-1", "name": "Pikachu", "set": {"id": "sv1", "name": "Escarlata", "series": "SV"}, "number": "1", "nationalPokedexNumbers": [25], "images": {"large": "https://example.com/card.png"}}], "pageSize": 100, "totalCount": 1}
        client = FakeClient({"cards": card_payload})
        sync_cards(client=client)
        card = TCGCard.objects.get(); card.custom_image = "cards/custom/manual.png"; card.save()
        sync_cards(client=client); card.refresh_from_db()
        self.assertEqual(card.custom_image.name, "cards/custom/manual.png")
        self.assertEqual(list(card.species.all()), [species])

    def test_card_sync_infers_species_when_api_omits_national_number(self):
        species = PokemonSpecies.objects.create(
            national_dex_number=1021,
            api_name="raging-bolt",
            display_name="Electrofuria",
        )
        payload = {
            "data": [{
                "id": "sv5-123",
                "name": "Raging Bolt ex",
                "supertype": "Pok\u00e9mon",
                "set": {"id": "sv5", "name": "Temporal Forces", "series": "SV"},
                "number": "123",
                "images": {},
            }],
            "pageSize": 100,
            "totalCount": 1,
        }

        summary = sync_cards(client=FakeClient({"cards": payload}))

        card = TCGCard.objects.get(external_id="sv5-123")
        self.assertEqual(list(card.species.all()), [species])
        self.assertEqual(summary["inferred"], 1)

    def test_card_sync_without_dex_numbers_preserves_manual_relationship(self):
        manual_species = PokemonSpecies.objects.create(
            national_dex_number=25,
            api_name="pikachu",
            display_name="Pikachu",
        )
        tcg_set = TCGSet.objects.create(external_id="manual", name="Manual", series="Test")
        card = TCGCard.objects.create(external_id="manual-1", name="Unknown Form", set=tcg_set)
        card.species.add(manual_species)
        payload = {
            "data": [{
                "id": "manual-1",
                "name": "Unknown Form",
                "supertype": "Pok\u00e9mon",
                "set": {"id": "manual", "name": "Manual", "series": "Test"},
                "images": {},
            }],
            "pageSize": 100,
            "totalCount": 1,
        }

        sync_cards(client=FakeClient({"cards": payload}))

        self.assertEqual(list(card.species.all()), [manual_species])

    def test_link_unlinked_cards_backfills_safe_name_matches(self):
        species = PokemonSpecies.objects.create(
            national_dex_number=1021,
            api_name="raging-bolt",
            display_name="Electrofuria",
        )
        tcg_set = TCGSet.objects.create(external_id="sv5", name="Temporal Forces", series="SV")
        card = TCGCard.objects.create(
            external_id="sv5-123",
            name="Raging Bolt ex",
            supertype="Pok\u00e9mon",
            set=tcg_set,
        )

        summary = link_unlinked_cards()

        self.assertEqual(list(card.species.all()), [species])
        self.assertEqual(summary["linked_cards"], 1)

    @patch("catalog.management.commands.sync_pokemon_species.sync_species", return_value={"created": 1, "updated": 0, "errors": 0})
    def test_management_command_uses_service(self, mocked):
        call_command("sync_pokemon_species", limit=1)
        mocked.assert_called_once_with(limit=1, missing_only=False)

    def test_species_sync_uses_default_variety_for_forms(self):
        client = FakeClient({
            "pokemon-species": {"results": [{"name": "deoxys", "url": "https://pokeapi.co/api/v2/pokemon-species/386/"}]},
            "pokemon-species/386/": {"id": 386, "name": "deoxys", "names": [], "generation": {"name": "generation-iii"}, "flavor_text_entries": [], "varieties": [{"is_default": True, "pokemon": {"url": "https://pokeapi.co/api/v2/pokemon/386/"}}]},
            "pokemon/386/": {"types": [{"slot": 1, "type": {"name": "psychic"}}]},
        })
        result = sync_species(client=client)
        self.assertEqual(result["created"], 1)
        self.assertEqual(PokemonSpecies.objects.get().primary_type, "psychic")
