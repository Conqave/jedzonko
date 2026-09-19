from households.application.access import HouseholdAccessPolicy
from recipes.application.errors import InvalidServingsError, RecipeNotFoundError
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from recipes.application.ports.recipe_repository import RecipeRepository
from recipes.application.ports.transaction_manager import TransactionManager
from recipes.domain.missing_items import scale_requirements


class ConfirmRecipePreparation:
    def __init__(
        self,
        repository: RecipeRepository,
        inventory_reader: HouseholdInventoryReader,
        inventory_consumer: HouseholdInventoryConsumer,
        transaction_manager: TransactionManager,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._repository = repository
        self._inventory_reader = inventory_reader
        self._inventory_consumer = inventory_consumer
        self._transaction_manager = transaction_manager
        self._access = access

    def execute(self, user_id: int, household_id: int, recipe_id: int, servings: int) -> None:
        self._access.require_membership(user_id, household_id)
        if servings < 1:
            raise InvalidServingsError
        recipe = self._repository.find_recipe(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError
        requirements = self._repository.list_requirements(recipe_id)
        scaled = scale_requirements(requirements, recipe.summary.servings, servings)
        with self._transaction_manager.atomic():
            inventory = self._inventory_reader.read_inventory(user_id, household_id)
            stocked_by_name = {item.normalized_name: item for item in inventory}
            for requirement in scaled:
                stocked = stocked_by_name.get(requirement.normalized_name)
                if stocked is None:
                    continue
                self._inventory_consumer.consume(
                    household_id,
                    stocked.product_id,
                    requirement.quantity.amount,
                    requirement.quantity.unit.code,
                )
