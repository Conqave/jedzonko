from dataclasses import dataclass

from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipePage


@dataclass(frozen=True, slots=True)
class ExternalRecipeQuery:
    text: str
    ingredient_names: tuple[str, ...]
    excluded_ingredient_names: tuple[str, ...]
    page: int
    page_size: int


class SearchExternalRecipes:
    def __init__(self, source: RecipeSource) -> None:
        self._source = source

    def execute(self, query: ExternalRecipeQuery) -> ExternalRecipePage:
        return self._source.search_recipes(
            query.text,
            query.ingredient_names,
            query.excluded_ingredient_names,
            query.page,
            query.page_size,
        )
