from shopping.application.errors import PrimaryShoppingListNotFoundError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.use_cases.add_missing_recipe_items_to_shopping_list import (
    AddMissingRecipeItemsToShoppingList,
)
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class AddMissingRecipeItemsToPrimaryList:

    def __init__(
        self,
        repository: ShoppingListRepository,
        add_missing: AddMissingRecipeItemsToShoppingList,
    ) -> None:
        self._repository = repository
        self._add_missing = add_missing

    def execute(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> list[ShoppingItemSnapshot]:
        primary = self._repository.find_primary_list(household_id)
        if primary is None:
            raise PrimaryShoppingListNotFoundError
        return self._add_missing.execute(user_id, primary.id, recipe_id, servings)
