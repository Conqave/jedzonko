from abc import ABC, abstractmethod

from inventory.domain.category import InventoryCategorySnapshot


class InventoryCategoryRepository(ABC):
    @abstractmethod
    def list_categories(self, household_id: int) -> list[InventoryCategorySnapshot]:
        raise NotImplementedError

    @abstractmethod
    def create_category(self, household_id: int, name: str) -> InventoryCategorySnapshot:
        raise NotImplementedError

    @abstractmethod
    def find_household_id_for_category(self, category_id: int) -> int | None:
        raise NotImplementedError
