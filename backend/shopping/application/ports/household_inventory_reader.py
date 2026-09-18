from abc import ABC, abstractmethod

from shopping.domain.inventory_stock_level import InventoryStockLevel


class HouseholdInventoryReader(ABC):
    @abstractmethod
    def read_stock_levels(self, user_id: int, household_id: int) -> list[InventoryStockLevel]:
        raise NotImplementedError
