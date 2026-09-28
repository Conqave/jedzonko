from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListNotFoundError
from shopping.application.items import ensure_on_list
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class AddMissingRecipeItemsToShoppingList:
    def __init__(
        self,
        repository: ShoppingListRepository,
        recipes: RecipeRequirementReader,
        catalog: CatalogDirectory,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._recipes = recipes
        self._catalog = catalog
        self._memberships = memberships
        self._transactions = transactions

    def execute(
        self, user_id: int, list_id: int, recipe_id: int, servings: int
    ) -> list[ShoppingItemSnapshot]:
        shopping_list = self._repository.find_list(list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        missing = self._recipes.get_missing_items(
            user_id, shopping_list.household_id, recipe_id, servings
        )
        with self._transactions.atomic():
            for item in missing:
                known_product = self._find_known_product(shopping_list.household_id, item)
                subject = item.subject(known_product)
                ensure_on_list(self._repository, list_id, subject, item.amount, item.unit_code)
        return self._repository.list_items(list_id)

    def _find_known_product(self, household_id: int, item: MissingRecipeItem) -> int | None:
        if item.stocked_product_id is not None or item.ingredient_id is None:
            return None
        return self._catalog.find_only_product_of_ingredient(household_id, item.ingredient_id)
