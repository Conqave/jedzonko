from households.application.access import HouseholdAccessPolicy
from recipes.application.errors import InvalidServingsError, RecipeNotFoundError
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.missing_items import calculate_shortfall, scale_requirements
from recipes.domain.suggestion import RecipeShortfall


class CalculateMissingRecipeItems:
    def __init__(
        self,
        repository: RecipeRepository,
        inventory_reader: HouseholdInventoryReader,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._repository = repository
        self._inventory_reader = inventory_reader
        self._access = access

    def execute(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> RecipeShortfall:
        self._access.require_membership(user_id, household_id)
        if servings < 1:
            raise InvalidServingsError
        recipe = self._repository.find_recipe(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError
        requirements = self._repository.list_requirements(recipe_id)
        scaled = scale_requirements(requirements, recipe.summary.servings, servings)
        inventory = self._inventory_reader.read_inventory(user_id, household_id)
        return calculate_shortfall(scaled, inventory)
