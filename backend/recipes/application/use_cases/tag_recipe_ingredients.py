from dataclasses import dataclass
from datetime import datetime

from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.recipe_repository import RecipeRepository


@dataclass(frozen=True, slots=True)
class RecipeTaggingRun:
    tagged: tuple[str, ...]
    untagged: tuple[str, ...]


class TagRecipeIngredients:
    def __init__(self, repository: RecipeRepository, lines: IngredientLines) -> None:
        self._repository = repository
        self._lines = lines

    def execute(self, now: datetime) -> RecipeTaggingRun:
        names = self._repository.list_untagged_ingredient_names()
        if not names:
            return RecipeTaggingRun(tagged=(), untagged=())
        self._lines.interpret(names, now)
        meanings = self._lines.find_interpretations(names)
        tagged: list[str] = []
        untagged: list[str] = []
        for name in names:
            meaning = meanings.get(name)
            if meaning is None or meaning.ingredient_id is None:
                untagged.append(name)
                continue
            self._repository.tag_ingredient_lines(name, meaning.ingredient_id)
            tagged.append(name)
        return RecipeTaggingRun(tagged=tuple(tagged), untagged=tuple(untagged))
