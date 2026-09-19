from abc import ABC, abstractmethod
from decimal import Decimal

from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_list_summary import ShoppingListSummary


class ShoppingListRepository(ABC):
    @abstractmethod
    def list_lists(self, household_id: int) -> list[ShoppingListSummary]:
        raise NotImplementedError

    @abstractmethod
    def get_or_create_primary_list(self, household_id: int) -> ShoppingListSummary:
        raise NotImplementedError

    @abstractmethod
    def create_list(self, household_id: int, name: str) -> ShoppingListSummary:
        raise NotImplementedError

    @abstractmethod
    def find_household_id_for_list(self, list_id: int) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def find_household_id_for_item(self, item_id: int) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def list_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def list_pending_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def find_pending_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def find_pending_item_by_ingredient(
        self, list_id: int, ingredient_id: int
    ) -> ShoppingItemSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def add_item(
        self,
        list_id: int,
        ingredient_id: int | None,
        free_text: str | None,
        quantity: Decimal,
        unit_code: str | None,
    ) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_item_quantity(
        self, item_id: int, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def purchase_item(self, item_id: int) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def delete_item(self, item_id: int) -> None:
        raise NotImplementedError
