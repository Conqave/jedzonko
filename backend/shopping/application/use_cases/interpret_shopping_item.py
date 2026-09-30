from datetime import datetime

from shared.household_membership import HouseholdMembershipReader, require_membership
from shopping.application.errors import ShoppingListItemNotFoundError, ShoppingListNotFoundError
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.line_interpreter import LineInterpreter
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.line_meaning import LineMeaning
from shopping.domain.shopping_item_interpretation import ShoppingItemInterpretation

UNKNOWN_MEANING = LineMeaning(ingredient_id=None, quantity=None, unit_code=None)


class InterpretShoppingItem:
    def __init__(
        self,
        repository: ShoppingListRepository,
        interpreter: LineInterpreter,
        catalog: CatalogDirectory,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._interpreter = interpreter
        self._catalog = catalog
        self._memberships = memberships

    def execute(self, user_id: int, item_id: int, now: datetime) -> ShoppingItemInterpretation:
        item = self._repository.find_item(item_id)
        if item is None or item.is_purchased:
            raise ShoppingListItemNotFoundError
        shopping_list = self._repository.find_list(item.list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        meanings = self._interpreter.interpret((item.name,), now)
        meaning = meanings.get(item.name, UNKNOWN_MEANING)
        ingredient_name = self._find_ingredient_name(meaning)
        ingredient_id = None if ingredient_name is None else meaning.ingredient_id
        return ShoppingItemInterpretation(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            quantity=meaning.quantity,
            unit_code=meaning.unit_code,
        )

    def _find_ingredient_name(self, meaning: LineMeaning) -> str | None:
        if meaning.ingredient_id is None:
            return None
        return self._catalog.find_ingredient_name(meaning.ingredient_id)
