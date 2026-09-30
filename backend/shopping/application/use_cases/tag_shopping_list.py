from datetime import datetime
from decimal import Decimal

from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingItemMergeConflictError, ShoppingListNotFoundError
from shopping.application.ports.line_interpreter import LineInterpreter
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.shopping_list_rules import put_tag_on_item
from shopping.domain.line_meaning import LineMeaning
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot

COUNT_UNIT = "szt"


class TagShoppingList:
    def __init__(
        self,
        repository: ShoppingListRepository,
        interpreter: LineInterpreter,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._interpreter = interpreter
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, list_id: int, now: datetime) -> list[ShoppingItemSnapshot]:
        shopping_list = self._repository.find_list(list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        return self.tag(list_id, now)

    def tag(self, list_id: int, now: datetime) -> list[ShoppingItemSnapshot]:
        texts = [
            item
            for item in self._repository.list_pending_items(list_id)
            if item.subject.free_text is not None
        ]
        if not texts:
            return self._repository.list_items(list_id)
        meanings = self._interpreter.interpret(tuple(item.name for item in texts), now)
        with self._transactions.atomic():
            for item in texts:
                meaning = meanings.get(item.name)
                if meaning is not None and meaning.ingredient_id is not None:
                    self._retag(item, meaning.ingredient_id, meaning)
        return self._repository.list_items(list_id)

    def _retag(self, item: ShoppingItemSnapshot, ingredient_id: int, meaning: LineMeaning) -> None:
        quantity, unit_code = _amount(item, meaning)
        try:
            put_tag_on_item(self._repository, item, ingredient_id, quantity, unit_code)
        except ShoppingItemMergeConflictError:
            return


def _amount(item: ShoppingItemSnapshot, meaning: LineMeaning) -> tuple[Decimal, str]:
    if meaning.quantity is not None and meaning.unit_code is not None:
        return meaning.quantity, meaning.unit_code
    if item.unit is not None:
        return item.quantity, item.unit.code
    return item.quantity, COUNT_UNIT


class TagAllShoppingLists:
    def __init__(self, repository: ShoppingListRepository, tag_list: TagShoppingList) -> None:
        self._repository = repository
        self._tag_list = tag_list

    def execute(self, now: datetime) -> int:
        list_ids = self._repository.list_ids_with_free_text()
        for list_id in list_ids:
            self._tag_list.tag(list_id, now)
        return len(list_ids)
