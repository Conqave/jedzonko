from abc import ABC, abstractmethod
from decimal import Decimal

from catalog.domain.measurement import MeasurementUnit


class InventoryWriter(ABC):
    @abstractmethod
    def add_purchased_quantity(
        self, household_id: int, ingredient_id: int, amount: Decimal, unit: MeasurementUnit
    ) -> None:
        raise NotImplementedError
