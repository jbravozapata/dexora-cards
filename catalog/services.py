import logging
import re
import time
import unicodedata
from datetime import datetime

import requests
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from .models import PokemonSpecies, TCGCard, TCGSet

logger = logging.getLogger(__name__)

CARD_MECHANIC_SUFFIX = re.compile(
    r"(?:\s+|\s*-\s*)(?:ex|gx|v|vmax|vstar|break|lv\.?\s*x|star)\s*$",
    re.IGNORECASE,
)


class APIClient:
    def __init__(self, base_url, headers=None, timeout=20, retries=3):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self.retries = retries

    def get(self, path, params=None):
        error = None
        for attempt in range(self.retries):
            try:
                response = requests.get(f"{self.base_url}/{path.lstrip('/')}", params=params, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("La API devolvió un formato inesperado")
                return data
            except (requests.RequestException, ValueError) as exc:
                error = exc
                if attempt + 1 < self.retries:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"No fue posible consultar {path}: {error}") from error


def generation_label(name):
    return name.replace("generation-", "Generación ").upper().replace("GENERACIÓN ", "Generación ")


def normalized_card_name(value):
    ascii_value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    return slugify(ascii_value)


def is_pokemon_card(supertype):
    return normalized_card_name(supertype) == "pokemon"


def species_name_index():
    return {
        normalized_card_name(species.api_name): species
        for species in PokemonSpecies.objects.filter(is_active=True)
    }


def infer_species_from_card_name(card_name, index=None):
    """Infer species only from Pokemon card titles when the API omits dex numbers."""
    index = index or species_name_index()
    cleaned = card_name or ""
    while CARD_MECHANIC_SUFFIX.search(cleaned):
        cleaned = CARD_MECHANIC_SUFFIX.sub("", cleaned).strip()
    segments = re.split(r"\s*(?:&|/)\s*", cleaned)
    inferred = []
    for segment in segments:
        normalized = normalized_card_name(segment)
        species = index.get(normalized)
        if species is None:
            suffix_matches = [
                (len(api_name), candidate)
                for api_name, candidate in index.items()
                if normalized.endswith(f"-{api_name}")
            ]
            if suffix_matches:
                species = max(suffix_matches, key=lambda item: item[0])[1]
        if species is not None and species not in inferred:
            inferred.append(species)
    return inferred


def link_unlinked_cards():
    index = species_name_index()
    summary = {
        "scanned": 0,
        "linked_cards": 0,
        "linked_relations": 0,
        "skipped_non_pokemon": 0,
        "unresolved_pokemon": 0,
    }
    cards = TCGCard.objects.filter(species__isnull=True).distinct().iterator(chunk_size=250)
    for card in cards:
        summary["scanned"] += 1
        if not is_pokemon_card(card.supertype):
            summary["skipped_non_pokemon"] += 1
            continue
        inferred = infer_species_from_card_name(card.name, index)
        if inferred:
            card.species.add(*inferred)
            summary["linked_cards"] += 1
            summary["linked_relations"] += len(inferred)
        else:
            summary["unresolved_pokemon"] += 1
    return summary


def sync_species(limit=None, client=None, missing_only=False):
    client = client or APIClient("https://pokeapi.co/api/v2")
    summary = {"created": 0, "updated": 0, "errors": 0, "skipped": 0}
    listing = client.get("pokemon-species", {"limit": limit or 2000, "offset": 0})
    rows = listing.get("results", [])[:limit] if limit else listing.get("results", [])
    for row in rows:
        try:
            dex_number_hint = int(row["url"].rstrip("/").rsplit("/", 1)[-1])
            existing = PokemonSpecies.objects.filter(national_dex_number=dex_number_hint).only("remote_artwork_url").first()
            if missing_only and existing and existing.remote_artwork_url:
                summary["skipped"] += 1
                continue
            detail = client.get(row["url"].replace("https://pokeapi.co/api/v2/", ""))
            dex_number = detail.get("id")
            if not dex_number:
                raise ValueError("Especie sin ID nacional")
            spanish = next((x["name"] for x in detail.get("names", []) if x.get("language", {}).get("name") == "es"), None)
            flavor = next((x["flavor_text"] for x in detail.get("flavor_text_entries", []) if x.get("language", {}).get("name") == "es"), "")
            default_variety = next((item for item in detail.get("varieties", []) if item.get("is_default")), None)
            pokemon_path = (
                default_variety["pokemon"]["url"].replace("https://pokeapi.co/api/v2/", "")
                if default_variety else f"pokemon/{detail.get('name')}"
            )
            pokemon = client.get(pokemon_path)
            types = sorted(pokemon.get("types", []), key=lambda x: x.get("slot", 0))
            sprites = pokemon.get("sprites") or {}
            other_sprites = sprites.get("other") or {}
            official_artwork = other_sprites.get("official-artwork") or {}
            home_artwork = other_sprites.get("home") or {}
            defaults = {
                "api_name": detail["name"],
                "display_name": spanish or detail["name"].replace("-", " ").title(),
                "generation": generation_label(detail.get("generation", {}).get("name", "")),
                "primary_type": types[0]["type"]["name"] if types else "",
                "secondary_type": types[1]["type"]["name"] if len(types) > 1 else "",
                "description": " ".join(flavor.replace("\n", " ").replace("\f", " ").split()),
                "external_url": row["url"],
                "remote_artwork_url": (
                    official_artwork.get("front_default")
                    or home_artwork.get("front_default")
                    or sprites.get("front_default")
                    or ""
                ),
            }
            obj, created = PokemonSpecies.objects.update_or_create(national_dex_number=dex_number, defaults=defaults)
            summary["created" if created else "updated"] += 1
        except Exception:
            logger.exception("Error sincronizando especie %s", row.get("name"))
            summary["errors"] += 1
    return summary


def sync_sets(client=None):
    headers = {"X-Api-Key": settings.POKEMON_TCG_API_KEY} if getattr(settings, "POKEMON_TCG_API_KEY", "") else {}
    client = client or APIClient("https://api.pokemontcg.io/v2", headers, timeout=30, retries=8)
    summary = {"created": 0, "updated": 0, "errors": 0}
    page = 1
    while True:
        payload = client.get("sets", {"page": page, "pageSize": 250, "orderBy": "releaseDate"})
        rows = payload.get("data", [])
        for row in rows:
            try:
                date = datetime.strptime(row["releaseDate"], "%Y/%m/%d").date() if row.get("releaseDate") else None
                _, created = TCGSet.objects.update_or_create(external_id=row["id"], defaults={
                    "name": row.get("name", ""), "series": row.get("series", ""),
                    "printed_total": row.get("printedTotal") or 0, "total": row.get("total") or 0,
                    "release_date": date, "symbol_url": row.get("images", {}).get("symbol", ""),
                    "logo_url": row.get("images", {}).get("logo", ""),
                })
                summary["created" if created else "updated"] += 1
            except Exception:
                logger.exception("Error sincronizando expansión %s", row.get("id")); summary["errors"] += 1
        if not rows or page * payload.get("pageSize", 250) >= payload.get("totalCount", 0): break
        page += 1
    return summary


def sync_cards(client=None, page_size=100, max_pages=None, start_page=1):
    headers = {"X-Api-Key": settings.POKEMON_TCG_API_KEY} if getattr(settings, "POKEMON_TCG_API_KEY", "") else {}
    client = client or APIClient("https://api.pokemontcg.io/v2", headers, timeout=30, retries=8)
    summary = {"created": 0, "updated": 0, "errors": 0, "unlinked": 0, "inferred": 0}
    name_index = species_name_index()
    page = max(start_page, 1)
    pages_processed = 0
    while True:
        payload = client.get("cards", {"page": page, "pageSize": page_size, "orderBy": "id"})
        rows = payload.get("data", [])
        for row in rows:
            try:
                with transaction.atomic():
                    set_data = row.get("set", {})
                    tcg_set, _ = TCGSet.objects.get_or_create(external_id=set_data["id"], defaults={"name": set_data.get("name", set_data["id"]), "series": set_data.get("series", "")})
                    defaults = {
                        "name": row.get("name", ""), "set": tcg_set, "number": row.get("number", ""),
                        "rarity": row.get("rarity", ""), "artist": row.get("artist", ""),
                        "supertype": row.get("supertype", ""), "subtypes": row.get("subtypes") or [],
                        "types": row.get("types") or [], "hp": row.get("hp", ""),
                        "remote_image_small": row.get("images", {}).get("small", ""),
                        "remote_image_large": row.get("images", {}).get("large", ""),
                    }
                    card, created = TCGCard.objects.update_or_create(external_id=row["id"], defaults=defaults)
                    numbers = row.get("nationalPokedexNumbers") or []
                    if numbers:
                        linked = list(PokemonSpecies.objects.filter(national_dex_number__in=numbers))
                        card.species.set(linked)
                        if not linked:
                            summary["unlinked"] += 1
                    elif not card.species.exists() and is_pokemon_card(row.get("supertype", "")):
                        inferred = infer_species_from_card_name(row.get("name", ""), name_index)
                        if inferred:
                            card.species.add(*inferred)
                            summary["inferred"] += len(inferred)
                        else:
                            summary["unlinked"] += 1
                    summary["created" if created else "updated"] += 1
            except Exception:
                logger.exception("Error sincronizando carta %s", row.get("id")); summary["errors"] += 1
        pages_processed += 1
        if not rows or page * payload.get("pageSize", page_size) >= payload.get("totalCount", 0) or (max_pages and pages_processed >= max_pages): break
        page += 1
    return summary
