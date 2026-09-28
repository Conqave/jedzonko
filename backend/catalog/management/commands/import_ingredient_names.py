import sys

from django.core.management.base import BaseCommand, CommandParser

from catalog.domain.ingredient import IngredientNameSource
from config.composition import container


class Command(BaseCommand):
    help = "Queue provider ingredient names, one per line on stdin, for curation in the admin."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--source",
            choices=[source.value for source in IngredientNameSource],
            default=IngredientNameSource.ANIA_GOTUJE.value,
        )

    def handle(self, *args: object, **options: object) -> None:
        names = tuple(line.strip() for line in sys.stdin if line.strip())
        source = IngredientNameSource(str(options["source"]))
        use_case = container().catalog.import_ingredient_names
        report = use_case.execute(names, source)
        self.stdout.write(
            f"Queued {len(report.created)}, already ingredients {len(report.already_known)}, "
            f"already queued {len(report.already_candidates)}."
        )
