from django.core.management.base import BaseCommand, CommandError
from catalog.services import sync_sets


class Command(BaseCommand):
    help = "Sincroniza expansiones desde Pokémon TCG API."

    def handle(self, *args, **options):
        try:
            result = sync_sets()
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Expansiones: {result}"))
