from abc import ABC, abstractmethod
from decimal import Decimal


class HouseholdInventoryConsumer(ABC):
    @abstractmethod
    def consume(self, household_id: int, product_id: int, amount: Decimal, unit_code: str) -> None:
        raise NotImplementedError
