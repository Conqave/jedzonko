from abc import ABC, abstractmethod

from shared.measurement import Quantity


class HouseholdInventoryConsumer(ABC):
    @abstractmethod
    def consume(self, household_id: int, product_id: int, quantity: Quantity) -> None:
        raise NotImplementedError
