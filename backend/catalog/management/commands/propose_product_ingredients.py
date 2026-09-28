from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from config.composition import container


class Command(BaseCommand):
    help = "Ask the local model which ingredient unclassified products are; stores proposals only."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: object, **options: object) -> None:
        dry_run = options["dry_run"] is True
        now = timezone.now()
        with container().catalog.open_classification() as classification:
            run = classification.execute(now, dry_run)
        verb = "Would propose" if dry_run else "Proposed"
        self.stdout.write(
            f"Asked {run.question_count} of at most {run.question_limit} question(s). "
            f"{verb} {len(run.proposals)} ingredient(s)."
        )
        for proposal in run.proposals:
            self.stdout.write(
                f"  product {proposal.product_id} -> ingredient {proposal.ingredient_id}"
            )
        if run.failure is not None:
            raise CommandError(f"The classifier failed: {run.failure}")
