from shared.household_membership import HouseholdMembershipReader, require_membership
from shopping.application.errors import ShoppingListNotFoundError
from shopping.application.item_calories import ShoppingCalorieCounter
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_listing import ShoppingItemListing


class GetShoppingListItems:
    def __init__(
        self,
        repository: ShoppingListRepository,
        calories: ShoppingCalorieCounter,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._calories = calories
        self._memberships = memberships

    def execute(self, user_id: int, list_id: int) -> list[ShoppingItemListing]:
        shopping_list = self._repository.find_list(list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        items = self._repository.list_items(list_id)
        return self._calories.count_many(shopping_list.household_id, items)
