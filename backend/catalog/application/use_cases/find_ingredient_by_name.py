from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient
from shared.text import normalize_text


class FindIngredientByName:

    def __init__(self, repository: IngredientRepository) -> None:
        self._repository = repository

    def execute(self, name: str) -> Ingredient | None:
        normalized_name = normalize_text(name)
        if not normalized_name:
            return None
        return self._repository.find_by_normalized_name(normalized_name)
