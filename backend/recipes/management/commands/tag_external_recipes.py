from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from config.composition import container
from recipes.application.errors import IngredientLineInterpreterError


class Command(BaseCommand):
    help = "Interpret the stored external recipe lines that are not interpreted yet, in batches."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--batch-size", type=int, default=20)
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args: object, **options: object) -> None:
        batch_size = options["batch_size"]
        limit = options["limit"]
        if not isinstance(batch_size, int) or not (limit is None or isinstance(limit, int)):
            raise CommandError("--batch-size and --limit must be numbers.")
        use_case = container().recipes.tag_external_recipe_lines
        try:
            run = use_case.execute(batch_size, limit, timezone.now(), self._report)
        except ValueError as error:
            raise CommandError(str(error)) from error
        except IngredientLineInterpreterError as error:
            raise CommandError(f"The model failed, run again to resume: {error}") from error
        self.stdout.write(
            f"Pending {run.pending_count}, processed {run.selected_count}, "
            f"interpreted {run.interpreted_count}."
        )

    def _report(self, done: int, total: int) -> None:
        self.stdout.write(f"  {done}/{total}")
