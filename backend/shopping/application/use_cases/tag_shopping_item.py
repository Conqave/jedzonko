from decimal import Decimal

from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListItemNotFoundError, ShoppingListNotFoundError
from shopping.application.item_calories import ShoppingCalorieCounter
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.shopping_list_rules import (
    put_tag_on_item,
    require_known_subject,
    require_valid_amount,
)
from shopping.domain.shopping_item_listing import ShoppingItemListing
from shopping.domain.shopping_subject import ShoppingSubject


class TagShoppingItem:
    def __init__(
        self,
        repository: ShoppingListRepository,
        catalog: CatalogDirectory,
        calories: ShoppingCalorieCounter,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._catalog = catalog
        self._calories = calories
        self._memberships = memberships
        self._transactions = transactions

    def execute(
        self, user_id: int, item_id: int, ingredient_id: int, quantity: Decimal, unit_code: str
    ) -> ShoppingItemListing:
        item = self._repository.find_item(item_id)
        if item is None or item.is_purchased:
            raise ShoppingListItemNotFoundError
        shopping_list = self._repository.find_list(item.list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        subject = ShoppingSubject(ingredient_id=ingredient_id)
        require_known_subject(self._catalog, shopping_list.household_id, subject)
        require_valid_amount(subject, quantity, unit_code)
        with self._transactions.atomic():
            tagged = put_tag_on_item(self._repository, item, ingredient_id, quantity, unit_code)
        return self._calories.count(shopping_list.household_id, tagged)
