from datetime import datetime

from recipes.application.external_ingredients import read_external_ingredients
from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.recipe_source import RecipeSource


class MatchExternalRecipeIngredients:
    def __init__(
        self, catalog: ExternalRecipeCatalog, source: RecipeSource, lines: IngredientLines
    ) -> None:
        self._catalog = catalog
        self._source = source
        self._lines = lines

    def execute(self, reference: str, now: datetime) -> int:
        ingredients = read_external_ingredients(self._catalog, self._source, reference)
        texts = tuple(line.source_text for line in ingredients)
        return self._lines.interpret(texts, now)
