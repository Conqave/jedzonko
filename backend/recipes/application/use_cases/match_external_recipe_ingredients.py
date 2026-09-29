from datetime import datetime

from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.recipe_source import RecipeSource


class MatchExternalRecipeIngredients:
    def __init__(self, source: RecipeSource, lines: IngredientLines) -> None:
        self._source = source
        self._lines = lines

    def execute(self, reference: str, now: datetime) -> int:
        recipe = self._source.get_recipe(reference)
        texts = tuple(line.source_text for line in recipe.ingredients)
        return self._lines.interpret(texts, now)
