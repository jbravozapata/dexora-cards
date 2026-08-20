from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import PokemonSpecies, TCGCard, TCGSet


SPECIES = [
    (1, "bulbasaur", "Bulbasaur", "planta", "veneno", "Un clásico compañero de Kanto."),
    (4, "charmander", "Charmander", "fuego", "", "Una especie emblemática de tipo Fuego."),
    (7, "squirtle", "Squirtle", "agua", "", "El Pokémon Tortuguita de Kanto."),
    (25, "pikachu", "Pikachu", "eléctrico", "", "Una de las especies más representadas en el TCG."),
    (133, "eevee", "Eevee", "incoloro", "", "Conocido por su gran potencial evolutivo."),
    (150, "mewtwo", "Mewtwo", "psíquico", "", "Una presencia poderosa en muchas expansiones."),
    (151, "mew", "Mew", "psíquico", "", "Una especie singular y muy buscada."),
    (252, "treecko", "Treecko", "planta", "", "Compañero inicial de Hoenn."),
    (393, "piplup", "Piplup", "agua", "", "Compañero inicial de Sinnoh."),
    (906, "sprigatito", "Sprigatito", "planta", "", "Compañero inicial de Paldea."),
]


class Command(BaseCommand):
    help = "Crea un catálogo demostrativo reproducible sin usar APIs ni imágenes oficiales."

    @transaction.atomic
    def handle(self, *args, **options):
        demo_set, _ = TCGSet.objects.update_or_create(external_id="demo-archive", defaults={
            "name": "Archivo de muestra", "series": "Demostración", "printed_total": 10,
            "total": 10, "release_date": date(2026, 1, 1),
        })
        for number, api_name, name, primary, secondary, description in SPECIES:
            species, _ = PokemonSpecies.objects.update_or_create(national_dex_number=number, defaults={
                "api_name": api_name, "display_name": name, "generation": "Generación I" if number <= 151 else "Generación IX",
                "primary_type": primary, "secondary_type": secondary, "description": description,
                "external_url": f"https://pokeapi.co/api/v2/pokemon-species/{number}/",
            })
            card, _ = TCGCard.objects.update_or_create(external_id=f"demo-{number}", defaults={
                "name": f"{name} · Estudio", "set": demo_set, "number": str(number), "rarity": "Muestra",
                "artist": "Sin ilustración oficial", "supertype": "Pokémon", "types": [primary.title()],
                "subtypes": ["Básico"], "hp": "—", "remote_image_small": "", "remote_image_large": "",
            })
            card.species.set([species])
        self.stdout.write(self.style.SUCCESS("Datos demo creados o actualizados: 10 especies y 10 cartas."))
