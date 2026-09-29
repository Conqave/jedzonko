from django.core.management.base import BaseCommand, CommandError, CommandParser

from catalog.application.errors import IngredientClassifierError
from config.composition import container


class Command(BaseCommand):
    help = "Ask the local model which similar tags are one ingredient and merge them."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: object, **options: object) -> None:
        dry_run = options["dry_run"] is True
        try:
            with container().catalog.open_tag_unification() as unification:
                run = unification.execute(dry_run)
        except IngredientClassifierError as error:
            raise CommandError(f"The model failed: {error}") from error
        verb = "Would merge" if dry_run else "Merged"
        for merge in run.merges:
            sources = ", ".join(source.name for source in merge.sources)
            self.stdout.write(f"{verb} {sources} -> {merge.target.name}")
