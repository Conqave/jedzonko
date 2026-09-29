from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_list_summary import ShoppingListSummary
from shopping.domain.shopping_subject import ShoppingSubject


class ShoppingListRepository(ABC):
    @abstractmethod
    def list_lists(self, household_id: int) -> list[ShoppingListSummary]:
        raise NotImplementedError

    @abstractmethod
    def find_list(self, list_id: int) -> ShoppingListSummary | None:
        raise NotImplementedError

    @abstractmethod
    def find_primary_list(self, household_id: int) -> ShoppingListSummary | None:
        raise NotImplementedError

    @abstractmethod
    def create_list(self, household_id: int, name: str, is_primary: bool) -> ShoppingListSummary:
        raise NotImplementedError

    @abstractmethod
    def rename_list(self, list_id: int, name: str) -> ShoppingListSummary:
        raise NotImplementedError

    @abstractmethod
    def delete_list(self, list_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def list_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def list_pending_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def find_pending_item(
        self, list_id: int, subject: ShoppingSubject
    ) -> ShoppingItemSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def add_item(
        self, list_id: int, subject: ShoppingSubject, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_item_quantity(
        self, item_id: int, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def mark_purchased(self, item_id: int, purchased_at: datetime) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def mark_pending(self, item_id: int) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def delete_item(self, item_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_items_about_ingredient(self, ingredient_id: int) -> list[ShoppingItemSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def set_item_product(self, item_id: int, product_id: int) -> ShoppingItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_item_ingredient(self, item_id: int, ingredient_id: int) -> None:
        raise NotImplementedError
