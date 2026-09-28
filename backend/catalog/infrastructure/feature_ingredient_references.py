from catalog.application.ports.ingredient_references import IngredientReferences
from recipes.application.use_cases.reassign_recipe_ingredient import ReassignRecipeIngredient
from shopping.application.use_cases.reassign_shopping_ingredient import ReassignShoppingIngredient


class RecipeIngredientReferences(IngredientReferences):
    def __init__(self, reassign: ReassignRecipeIngredient) -> None:
        self._reassign = reassign

    def reassign(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        self._reassign.execute(source_ingredient_id, target_ingredient_id)


class ShoppingIngredientReferences(IngredientReferences):
    def __init__(self, reassign: ReassignShoppingIngredient) -> None:
        self._reassign = reassign

    def reassign(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        self._reassign.execute(source_ingredient_id, target_ingredient_id)
