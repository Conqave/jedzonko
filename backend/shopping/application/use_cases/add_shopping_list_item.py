from decimal import Decimal

from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListNotFoundError
from shopping.application.items import add_to_list, require_known_subject, require_valid_amount
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_subject import ShoppingSubject


class AddShoppingListItem:
    def __init__(
        self,
        repository: ShoppingListRepository,
        catalog: CatalogDirectory,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._catalog = catalog
        self._memberships = memberships
        self._transactions = transactions

    def execute(
        self,
        user_id: int,
        list_id: int,
        subject: ShoppingSubject,
        quantity: Decimal,
        unit_code: str | None,
    ) -> ShoppingItemSnapshot:
        shopping_list = self._repository.find_list(list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        require_valid_amount(subject, quantity, unit_code)
        require_known_subject(self._catalog, shopping_list.household_id, subject)
        with self._transactions.atomic():
            return add_to_list(self._repository, list_id, subject, quantity, unit_code)
