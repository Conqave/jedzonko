from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from households.analysis_composition import (
    build_analyze_unmatched_ingredients,
    open_ingredient_matcher,
)
from households.domain.alias_analysis import AliasAnalysisReport


class Command(BaseCommand):
    help = (
        "Asks the configured local model which pantry product each unmatched recipe "
        "ingredient is, and stores the answers as pending alias proposals."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: object, **options: object) -> None:
        dry_run = options["dry_run"] is True
        with open_ingredient_matcher() as matcher:
            report = build_analyze_unmatched_ingredients(matcher).execute(timezone.now(), dry_run)
        self._print_report(report, dry_run)
        if report.failure is not None:
            raise CommandError(f"Ingredient matcher failed: {report.failure}")

    def _print_report(self, report: AliasAnalysisReport, dry_run: bool) -> None:
        verb = "Would propose" if dry_run else "Proposed"
        self.stdout.write(
            f"Asked {report.question_count} of at most {report.question_limit} question(s) "
            f"across {len(report.households)} household(s)."
        )
        for analysis in report.households:
            self.stdout.write(
                f"Household {analysis.household_id} '{analysis.household_name}': "
                f"{analysis.unmatched_requirement_count} unmatched requirement(s), "
                f"{analysis.question_count} question(s), "
                f"{len(analysis.proposals)} proposal(s)."
            )
            for proposal in analysis.proposals:
                self.stdout.write(
                    f"  {verb} '{proposal.requirement_name}' -> "
                    f"'{proposal.product_name}' (product {proposal.product_id}, "
                    f"model {proposal.model_name})."
                )
        if report.limit_reached:
            self.stdout.write(
                "Question limit reached; remaining households are left for the next run."
            )
