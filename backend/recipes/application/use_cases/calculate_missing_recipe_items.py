from recipes.application.errors import InvalidServingsError, RecipeNotFoundError
from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.missing_items import calculate_shortfall, scale_requirements
from recipes.domain.suggestion import RecipeShortfall
from shared.household_membership import HouseholdMembershipReader, require_membership


class CalculateMissingRecipeItems:
    def __init__(
        self,
        repository: RecipeRepository,
        stock: HouseholdStockReader,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._stock = stock
        self._memberships = memberships

    def execute(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> RecipeShortfall:
        require_membership(self._memberships, user_id, household_id)
        if servings < 1:
            raise InvalidServingsError
        recipe = self._repository.find_recipe(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError
        requirements = self._repository.list_requirements(recipe_id)
        scaled = scale_requirements(requirements, recipe.summary.servings, servings)
        stock = self._stock.get_stock(user_id, household_id)
        return calculate_shortfall(scaled, stock)
