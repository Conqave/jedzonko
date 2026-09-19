from recipes.composition import build_calculate_missing_recipe_items
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.domain.missing_recipe_item import MissingRecipeItem


class RecipeRequirementGateway(RecipeRequirementReader):
    def read_missing_items(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> list[MissingRecipeItem]:
        missing = build_calculate_missing_recipe_items().execute(
            user_id, household_id, recipe_id, servings
        )
        return [
            MissingRecipeItem(
                name=item.name,
                normalized_name=item.normalized_name,
                amount=item.amount,
                unit_code=item.unit_code,
            )
            for item in missing
        ]
