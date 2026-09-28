from abc import ABC, abstractmethod

from recipes.domain.stock import StockedProduct


class HouseholdStockReader(ABC):
    @abstractmethod
    def get_stock(self, user_id: int, household_id: int) -> list[StockedProduct]:
        raise NotImplementedError
