from django.core.management.base import BaseCommand, CommandError, CommandParser

from catalog.application.errors import IngredientNotFoundError
from config.composition import container


class Command(BaseCommand):
    help = "Turn an alias that was merged by mistake back into a tag of its own."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("aliases", nargs="+")

    def handle(self, *args: object, **options: object) -> None:
        aliases = options["aliases"]
        if not isinstance(aliases, list):
            raise CommandError("Give at least one alias.")
        for alias in aliases:
            try:
                ingredient = container().catalog.split_alias.execute(str(alias))
            except IngredientNotFoundError as error:
                raise CommandError(f"No alias named {alias!r}.") from error
            self.stdout.write(f"'{ingredient.name}' is a tag of its own again ({ingredient.id}).")
