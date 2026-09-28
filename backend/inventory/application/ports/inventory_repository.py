from abc import ABC, abstractmethod
from decimal import Decimal

from inventory.domain.models import InventoryItemSnapshot
from inventory.domain.photo import InventoryPhoto


class InventoryRepository(ABC):
    @abstractmethod
    def list_items(self, household_id: int) -> list[InventoryItemSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def find_item(self, item_id: int) -> InventoryItemSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def find_household_id_for_item(self, item_id: int) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def find_item_by_product(self, product_id: int) -> InventoryItemSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def lock_item_by_product(self, product_id: int) -> InventoryItemSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def create_item(
        self,
        product_id: int,
        quantity: Decimal,
        unit_code: str,
        minimum_quantity: Decimal | None,
        category_id: int | None,
    ) -> InventoryItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_quantity(self, item_id: int, quantity: Decimal) -> InventoryItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def update_item(
        self, item_id: int, quantity: Decimal | None, unit_code: str | None
    ) -> InventoryItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_category(self, item_id: int, category_id: int | None) -> InventoryItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def set_photo(self, item_id: int, photo: InventoryPhoto) -> InventoryItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def clear_photo(self, item_id: int) -> InventoryItemSnapshot:
        raise NotImplementedError

    @abstractmethod
    def delete_item(self, item_id: int) -> None:
        raise NotImplementedError
