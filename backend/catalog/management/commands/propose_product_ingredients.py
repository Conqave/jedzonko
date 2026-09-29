from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from config.composition import container


class Command(BaseCommand):
    help = "Ask the local model for the tags of untagged products and assign them."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--question-limit", type=int, default=settings.INGREDIENT_CLASSIFIER_QUESTION_LIMIT
        )

    def handle(self, *args: object, **options: object) -> None:
        dry_run = options["dry_run"] is True
        now = timezone.now()
        question_limit = options["question_limit"]
        if not isinstance(question_limit, int):
            raise CommandError("--question-limit must be a number.")
        with container().catalog.open_classification(question_limit) as classification:
            run = classification.execute(now, dry_run)
        verb = "Would assign" if dry_run else "Assigned"
        self.stdout.write(
            f"Asked {run.question_count} of at most {run.question_limit} question(s). "
            f"{verb} {len(run.proposals)} tag(s)."
        )
        for proposal in run.proposals:
            self.stdout.write(
                f"  product {proposal.product_id} -> ingredient {proposal.ingredient_id}"
            )
        if run.failure is not None:
            raise CommandError(f"The classifier failed: {run.failure}")
