from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from config.composition import container
from recipes.application.errors import IngredientLineInterpreterError


class Command(BaseCommand):
    help = "Tag the ingredients of own recipes that no tag was found for yet."

    def handle(self, *args: object, **options: object) -> None:
        try:
            run = container().recipes.tag_recipe_ingredients.execute(timezone.now())
        except IngredientLineInterpreterError as error:
            raise CommandError(f"The model failed: {error}") from error
        self.stdout.write(f"Tagged {len(run.tagged)}, still untagged {len(run.untagged)}.")
        for name in run.untagged:
            self.stdout.write(f"  ? {name}")
