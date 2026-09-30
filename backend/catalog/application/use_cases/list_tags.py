from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient


class ListTags:
    def __init__(self, ingredients: IngredientRepository) -> None:
        self._ingredients = ingredients

    def execute(self) -> tuple[Ingredient, ...]:
        tags = self._ingredients.list_tags()
        return tuple(tags)
