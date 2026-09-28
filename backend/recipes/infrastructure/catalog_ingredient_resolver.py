from catalog.application.use_cases.find_ingredients_by_names import FindIngredientsByNames
from recipes.application.ports.ingredient_resolver import IngredientResolver


class CatalogIngredientResolver(IngredientResolver):
    def __init__(self, find_ingredients: FindIngredientsByNames) -> None:
        self._find_ingredients = find_ingredients

    def find_ingredient_ids(self, names: tuple[str, ...]) -> dict[str, int]:
        found = self._find_ingredients.execute(names)
        return {name: ingredient.id for name, ingredient in found.items()}
