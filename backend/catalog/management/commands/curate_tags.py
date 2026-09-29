from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from catalog.application.errors import IngredientClassifierError
from config.composition import container


class Command(BaseCommand):
    help = "Let the local model turn pending tag candidates into tags, aliases or dismissals."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--batch-size", type=int, default=40)
        parser.add_argument("--limit", type=int, default=2000)

    def handle(self, *args: object, **options: object) -> None:
        batch_size = options["batch_size"]
        limit = options["limit"]
        if not isinstance(batch_size, int) or not isinstance(limit, int):
            raise CommandError("--batch-size and --limit must be numbers.")
        now = timezone.now()
        try:
            with container().catalog.open_candidate_curation(batch_size) as curation:
                run = curation.execute(now, limit)
        except IngredientClassifierError as error:
            raise CommandError(f"The model failed: {error}") from error
        self.stdout.write(
            f"New tags {len(run.new_tags)}, aliases {len(run.aliases)}, "
            f"dismissed {len(run.dismissed)}, skipped {len(run.skipped)}."
        )
        for line in (*run.aliases, *(f"+ {name}" for name in run.new_tags)):
            self.stdout.write(f"  {line}")
        for line in run.dismissed:
            self.stdout.write(f"  - {line}")
        for line in run.skipped:
            self.stdout.write(f"  ? {line}")
