from django.core.management.base import BaseCommand

from catalog.services import link_unlinked_cards


class Command(BaseCommand):
    help = "Relaciona cartas Pokemon sin numero nacional usando coincidencias seguras de nombre."

    def handle(self, *args, **options):
        result = link_unlinked_cards()
        self.stdout.write(self.style.SUCCESS(f"Relaciones TCG: {result}"))
