from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from households.composition import build_purge_expired_households
from households.domain.retention import HOUSEHOLD_RETENTION_PERIOD


class Command(BaseCommand):
    help = "Permanently purges households deleted longer ago than the recovery window."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: object, **options: object) -> None:
        dry_run = options["dry_run"] is True
        households = build_purge_expired_households().execute(timezone.now(), dry_run)
        verb = "Would purge" if dry_run else "Purged"
        self.stdout.write(
            f"Retention window: {HOUSEHOLD_RETENTION_PERIOD.days} days. "
            f"{verb} {len(households)} household(s)."
        )
        for household in households:
            self.stdout.write(
                f"{verb} household {household.id} '{household.name}' "
                f"deleted at {household.deleted_at.isoformat()}."
            )
