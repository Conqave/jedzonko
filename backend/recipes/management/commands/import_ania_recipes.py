from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from config.composition import container
from recipes.application.errors import RecipeSourceError
from recipes.application.use_cases.import_external_recipes import ImportOutcome


class Command(BaseCommand):
    help = (
        "Import the ingredient lines of all Ania Gotuje recipes listed in the site map, "
        "one page at a time. Already stored recipes are skipped unless --refresh is given."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--refresh", action="store_true")
        parser.add_argument("--delay", type=float, default=1.5)
        parser.add_argument("--attempts", type=int, default=4)

    def handle(self, *args: object, **options: object) -> None:
        limit = options["limit"]
        refresh = options["refresh"]
        delay = options["delay"]
        attempts = options["attempts"]
        if not (limit is None or isinstance(limit, int)) or not isinstance(refresh, bool):
            raise CommandError("--limit must be a number.")
        if not isinstance(delay, float) or not isinstance(attempts, int):
            raise CommandError("--delay and --attempts must be numbers.")
        try:
            with container().recipes.open_import(delay, attempts) as import_recipes:
                run = import_recipes.execute(limit, refresh, timezone.now(), self._report)
        except ValueError as error:
            raise CommandError(str(error)) from error
        except RecipeSourceError as error:
            raise CommandError(f"Import stopped, run again to resume: {error}") from error
        self.stdout.write(
            f"Listed {run.listed_count}, already stored {run.skipped_count}, "
            f"imported {run.count(ImportOutcome.IMPORTED)}, "
            f"without image {run.count(ImportOutcome.IMPORTED_WITHOUT_IMAGE)}, "
            f"images added {run.count(ImportOutcome.IMAGE_ADDED)}, "
            f"images failed {run.count(ImportOutcome.IMAGE_FAILED)}, "
            f"missing {run.count(ImportOutcome.MISSING)}, "
            f"rejected {run.count(ImportOutcome.REJECTED)}."
        )

    def _report(self, reference: str, outcome: ImportOutcome) -> None:
        self.stdout.write(f"  {outcome.value:<12} {reference}")
