from recipes.application.errors import InvalidServingsError, RecipeNotFoundError
from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.domain.matching import consumption_in_stock_unit, find_stock
from recipes.domain.missing_items import scale_requirements
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager


class ConfirmRecipePreparation:

    def __init__(
        self,
        repository: RecipeRepository,
        stock: HouseholdStockReader,
        consumer: HouseholdInventoryConsumer,
        transactions: TransactionManager,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._stock = stock
        self._consumer = consumer
        self._transactions = transactions
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int, recipe_id: int, servings: int) -> None:
        require_membership(self._memberships, user_id, household_id)
        if servings < 1:
            raise InvalidServingsError
        recipe = self._repository.find_recipe(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError
        requirements = self._repository.list_requirements(recipe_id)
        scaled = scale_requirements(requirements, recipe.summary.servings, servings)
        with self._transactions.atomic():
            stock = self._stock.get_stock(user_id, household_id)
            for requirement in scaled:
                match = find_stock(requirement.ingredient_id, requirement.quantity.unit, stock)
                if match is None:
                    continue
                used = consumption_in_stock_unit(match.product, requirement.quantity)
                if used is None:
                    continue
                self._consumer.consume(household_id, match.product.product_id, used)
