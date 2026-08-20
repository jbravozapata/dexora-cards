from django.core.management.base import BaseCommand, CommandError
from catalog.services import sync_species


class Command(BaseCommand):
    help = "Sincroniza especies nacionales desde PokéAPI."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limita especies para pruebas.")
        parser.add_argument("--missing-only", action="store_true", help="Omite números nacionales ya presentes.")

    def handle(self, *args, **options):
        try:
            result = sync_species(limit=options["limit"], missing_only=options["missing_only"])
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Especies: {result}"))
