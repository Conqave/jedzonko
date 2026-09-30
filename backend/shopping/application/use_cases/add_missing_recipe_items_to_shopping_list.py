from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListNotFoundError
from shopping.application.item_calories import ShoppingCalorieCounter
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.shopping_list_rules import put_missing_items_on_list
from shopping.domain.shopping_item_listing import ShoppingItemListing


class AddMissingRecipeItemsToShoppingList:
    def __init__(
        self,
        repository: ShoppingListRepository,
        recipes: RecipeRequirementReader,
        catalog: CatalogDirectory,
        calories: ShoppingCalorieCounter,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._recipes = recipes
        self._catalog = catalog
        self._calories = calories
        self._memberships = memberships
        self._transactions = transactions

    def execute(
        self, user_id: int, list_id: int, recipe_id: int, servings: int
    ) -> list[ShoppingItemListing]:
        shopping_list = self._repository.find_list(list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        missing = self._recipes.get_missing_items(
            user_id, shopping_list.household_id, recipe_id, servings
        )
        with self._transactions.atomic():
            put_missing_items_on_list(
                self._repository, self._catalog, shopping_list.household_id, list_id, missing
            )
        items = self._repository.list_items(list_id)
        return self._calories.count_many(shopping_list.household_id, items)
