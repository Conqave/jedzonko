from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient
from shared.text import normalize_text


class FindIngredientsByNames:

    def __init__(self, ingredients: IngredientRepository) -> None:
        self._ingredients = ingredients

    def execute(self, names: tuple[str, ...]) -> dict[str, Ingredient]:
        normalized = {name: normalize_text(name) for name in names}
        found = self._ingredients.find_by_normalized_names(
            {value for value in normalized.values() if value}
        )
        return {
            name: found[normalized_name]
            for name, normalized_name in normalized.items()
            if normalized_name in found
        }
