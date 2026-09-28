from django.core.management.base import BaseCommand, CommandError, CommandParser

from config.composition import container


class Command(BaseCommand):
    help = "Merge a duplicate ingredient into another; every reference moves to the target."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("source_id", type=int)
        parser.add_argument("target_id", type=int)

    def handle(self, *args: object, **options: object) -> None:
        source_id = options["source_id"]
        target_id = options["target_id"]
        if not isinstance(source_id, int) or not isinstance(target_id, int):
            raise CommandError("Ingredient ids must be integers.")
        use_case = container().catalog.merge_ingredients
        target = use_case.execute(source_id, target_id)
        self.stdout.write(f"Merged ingredient {source_id} into {target.id} '{target.name}'.")
