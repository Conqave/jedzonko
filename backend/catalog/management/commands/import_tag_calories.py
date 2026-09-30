from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser

from catalog.application.errors import DuplicateTagReferenceError
from catalog.presentation.calorie_reference_file import read_calorie_references
from catalog.presentation.reference_file import InvalidReferenceFileError
from catalog.presentation.reference_report import write_reference_report
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
        except InvalidReferenceFileError as error:
            raise CommandError(f"{path}: {error}") from error
        use_case = container().catalog.import_tag_calories
        try:
            run = use_case.execute(references)
        except DuplicateTagReferenceError as error:
            raise CommandError(f"Nothing imported: {error}") from error
        write_reference_report(run, self.stdout)
