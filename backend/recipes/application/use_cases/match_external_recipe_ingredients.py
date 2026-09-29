from datetime import datetime

from recipes.application.ports.ingredient_line_interpreter import IngredientLineInterpreter
from recipes.application.ports.ingredient_line_repository import IngredientLineRepository
from recipes.application.ports.recipe_source import RecipeSource
from recipes.application.ports.tag_vocabulary import TagVocabulary
from recipes.domain.external_line import (
    MAX_LINE_TEXT_LENGTH,
    LineInterpretation,
)
from shared.text import normalize_text


class MatchExternalRecipeIngredients:
    def __init__(
        self,
        source: RecipeSource,
        vocabulary: TagVocabulary,
        lines: IngredientLineRepository,
        interpreter: IngredientLineInterpreter,
    ) -> None:
        self._source = source
        self._vocabulary = vocabulary
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
        choices = self._vocabulary.list_tags()
        if not choices:
            return 0
        unknown_lines = tuple(line for line in unknown.values())
        interpretations = self._interpreter.interpret(unknown_lines, choices)
        pairs = zip(unknown, interpretations, strict=True)
        interpreted: dict[str, LineInterpretation] = dict(pairs)
        self._lines.save_interpretations(interpreted, self._interpreter.model_name, now)
        return len(interpreted)
