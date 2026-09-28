from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.missing_items import calculate_shortfall
from recipes.domain.ranking import rank_suggestions
from recipes.domain.suggestion import RecipeSuggestion
from shared.household_membership import HouseholdMembershipReader, require_membership


class SuggestRecipesFromInventory:
    def __init__(
        self,
        repository: RecipeRepository,
        stock: HouseholdStockReader,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._stock = stock
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int) -> list[RecipeSuggestion]:
        require_membership(self._memberships, user_id, household_id)
        stock = self._stock.get_stock(user_id, household_id)
        requirements_by_recipe = self._repository.list_requirements_by_recipe()
        suggestions: list[RecipeSuggestion] = []
        for recipe in self._repository.list_recipes():
            requirements = requirements_by_recipe.get(recipe.id, [])
            shortfall = calculate_shortfall(requirements, stock)
            suggestions.append(
                RecipeSuggestion(recipe_id=recipe.id, recipe_name=recipe.name, shortfall=shortfall)
            )
        return rank_suggestions(suggestions)
