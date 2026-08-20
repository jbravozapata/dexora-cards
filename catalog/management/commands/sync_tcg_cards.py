from django.core.management.base import BaseCommand, CommandError
from catalog.services import sync_cards


class Command(BaseCommand):
    help = "Sincroniza cartas por lotes desde Pokémon TCG API."

    def add_arguments(self, parser):
        parser.add_argument("--page-size", type=int, default=100)
        parser.add_argument("--max-pages", type=int)
        parser.add_argument("--start-page", type=int, default=1)

    def handle(self, *args, **options):
        try:
            result = sync_cards(
                page_size=options["page_size"],
                max_pages=options["max_pages"],
                start_page=options["start_page"],
            )
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Cartas: {result}"))
