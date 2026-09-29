from datetime import datetime

from recipes.application.ports.ingredient_line_interpreter import IngredientLineInterpreter
from recipes.application.ports.ingredient_line_repository import IngredientLineRepository
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external_line import (
    MAX_LINE_TEXT_LENGTH,
    IngredientChoice,
    LineInterpretation,
)
from shared.text import normalize_text


class MatchExternalRecipeIngredients:
    def __init__(
        self,
        source: RecipeSource,
        resolver: IngredientResolver,
        lines: IngredientLineRepository,
        interpreter: IngredientLineInterpreter,
    ) -> None:
        self._source = source
        self._resolver = resolver
        self._lines = lines
        self._interpreter = interpreter

    def execute(self, reference: str, now: datetime) -> int:
        recipe = self._source.get_recipe(reference)
        texts = tuple(normalize_text(line.source_text) for line in recipe.ingredients)
        known = self._lines.find_interpretations(texts)
        unknown = {
            text: line.source_text
            for text, line in zip(texts, recipe.ingredients, strict=True)
            if text not in known and len(text) <= MAX_LINE_TEXT_LENGTH
        }
        if not unknown:
            return 0
        ingredient_ids = self._resolver.find_ingredient_ids(recipe.summary.tag_names)
        choices = tuple(
            IngredientChoice(id=ingredient_id, name=name)
            for name, ingredient_id in ingredient_ids.items()
        )
        if not choices:
            return 0
        unknown_lines = tuple(line for line in unknown.values())
        interpretations = self._interpreter.interpret(unknown_lines, choices)
        pairs = zip(unknown, interpretations, strict=True)
        interpreted: dict[str, LineInterpretation] = dict(pairs)
        self._lines.save_interpretations(interpreted, self._interpreter.model_name, now)
        return len(interpreted)
