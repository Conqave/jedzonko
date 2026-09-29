from django.core.management.base import BaseCommand
from django.utils import timezone

from config.composition import container


class Command(BaseCommand):
    help = "Tag the free-text items of every shopping list with the catalog vocabulary."

    def handle(self, *args: object, **options: object) -> None:
        count = container().shopping.tag_all_shopping_lists.execute(timezone.now())
        self.stdout.write(f"Tagged free-text items on {count} list(s).")
