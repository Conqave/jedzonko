from decimal import Decimal

from inventory.application.errors import InventoryItemNotFoundError
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.transaction_manager import TransactionManager
from inventory.domain.models import InventoryItemSnapshot
from shared.measurement import MeasurementUnit, Quantity

EMPTY = Decimal("0")


class ConsumeInventoryQuantity:
    def __init__(
        self, repository: InventoryRepository, transaction_manager: TransactionManager
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager

    def execute(
        self,
        household_id: int,
        product_id: int,
        amount: Decimal,
        unit: MeasurementUnit,
    ) -> InventoryItemSnapshot:
        with self._transaction_manager.atomic():
            existing = self._repository.lock_item_by_product(household_id, product_id)
            if existing is None:
                raise InventoryItemNotFoundError
            remaining = existing.as_quantity().subtract(Quantity(amount=amount, unit=unit))
            floored = remaining.amount if remaining.amount > EMPTY else EMPTY
            return self._repository.set_quantity(existing.id, floored)
