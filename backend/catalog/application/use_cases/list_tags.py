from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient, IngredientNameKind


class ListTags:
    def __init__(self, ingredients: IngredientRepository) -> None:
        self._ingredients = ingredients

    def execute(self) -> tuple[Ingredient, ...]:
        names = self._ingredients.list_names()
        canonical = [name for name in names if name.kind is IngredientNameKind.CANONICAL]
        ordered = sorted(canonical, key=lambda name: name.normalized_name)
        return tuple(Ingredient(id=name.ingredient_id, name=name.name) for name in ordered)
