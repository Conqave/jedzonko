from households.application.access import HouseholdAccessPolicy
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.missing_items import calculate_shortfall
from recipes.domain.ranking import rank_suggestions
from recipes.domain.suggestion import RecipeSuggestion


class SuggestRecipesFromInventory:
    def __init__(
        self,
        repository: RecipeRepository,
        inventory_reader: HouseholdInventoryReader,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._repository = repository
        self._inventory_reader = inventory_reader
        self._access = access

    def execute(self, user_id: int, household_id: int) -> list[RecipeSuggestion]:
        self._access.require_membership(user_id, household_id)
        inventory = self._inventory_reader.read_inventory(user_id, household_id)
        recipes = self._repository.list_recipes()
        requirements_by_recipe = self._repository.list_requirements_by_recipe()
        suggestions = [
            RecipeSuggestion(
                recipe_id=recipe.id,
                recipe_name=recipe.name,
                shortfall=calculate_shortfall(requirements_by_recipe.get(recipe.id, []), inventory),
            )
            for recipe in recipes
        ]
        return rank_suggestions(suggestions)
