from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient
from shared.text import normalize_text

SEARCH_RESULT_LIMIT = 20


class SearchIngredients:

    def __init__(self, ingredients: IngredientRepository) -> None:
        self._ingredients = ingredients

    def execute(self, query: str) -> list[Ingredient]:
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []
        return self._ingredients.search(normalized_query, SEARCH_RESULT_LIMIT)
