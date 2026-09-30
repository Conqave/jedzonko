from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser

from catalog.application.errors import DuplicateCalorieReferenceError
from catalog.presentation.calorie_reference_file import (
    InvalidCalorieReferenceFileError,
    read_calorie_references,
)
from config.composition import container


class Command(BaseCommand):
    help = "Import researched calories per 100 g of tags from a tag,kcal_per_100g,source_url CSV."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=Path)

    def handle(self, *args: object, **options: object) -> None:
        path = options["path"]
        if not isinstance(path, Path):
            raise CommandError("The path must name a CSV file.")
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                references = read_calorie_references(stream)
        except OSError as error:
            raise CommandError(f"Cannot read {path}: {error}") from error
        except InvalidCalorieReferenceFileError as error:
            raise CommandError(f"{path}: {error}") from error
        use_case = container().catalog.import_tag_calories
        try:
            run = use_case.execute(references)
        except DuplicateCalorieReferenceError as error:
            raise CommandError(f"Nothing imported: {error}") from error
        self.stdout.write(
            f"Updated {len(run.updated)}, unchanged {len(run.unchanged)}, "
            f"skipped manual {len(run.skipped_manual)}, unknown {len(run.unknown)}."
        )
        for name in run.updated:
            self.stdout.write(f"  + {name}")
        for name in run.skipped_manual:
            self.stdout.write(f"  = {name} (manual value kept)")
        for name in run.unknown:
            self.stdout.write(f"  ? {name}")
