from abc import ABC, abstractmethod

from inventory.domain.models import InventoryItemSnapshot


class HouseholdInventoryReader(ABC):
    @abstractmethod
    def read_inventory(self, user_id: int, household_id: int) -> list[InventoryItemSnapshot]:
        raise NotImplementedError
