from django.db import transaction

from households.application.access import HouseholdAccessPolicy
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_list_summary import ShoppingListSummary


class ListShoppingLists:
    def __init__(self, repository: ShoppingListRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, household_id: int) -> list[ShoppingListSummary]:
        self._access.require_membership(user_id, household_id)
        with transaction.atomic():
            self._repository.get_or_create_primary_list(household_id)
        return self._repository.list_lists(household_id)
