from recipes.application.use_cases.calculate_missing_recipe_items import (
    CalculateMissingRecipeItems,
)
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.domain.missing_recipe_item import MissingRecipeItem


class RecipeRequirementGateway(RecipeRequirementReader):
    def __init__(self, calculate_missing: CalculateMissingRecipeItems) -> None:
        self._calculate_missing = calculate_missing

    def get_missing_items(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> list[MissingRecipeItem]:
        shortfall = self._calculate_missing.execute(user_id, household_id, recipe_id, servings)
        return [
            MissingRecipeItem(
                name=item.name,
                ingredient_id=item.ingredient_id,
                stocked_product_id=item.stocked_product_id,
                amount=item.amount,
                unit_code=item.unit_code,
            )
            for item in shortfall.missing_items
        ]
