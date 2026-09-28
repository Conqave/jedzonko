from decimal import Decimal

from inventory.application.errors import InventoryItemNotFoundError, ProductNotFoundError
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.product_directory import ProductDirectory
from inventory.domain.models import InventoryItemSnapshot
from shared.measurement import MeasurementUnit, Quantity
from shared.transactions import TransactionManager

EMPTY = Decimal("0")


class ConsumeInventoryQuantity:
    def __init__(
        self,
        repository: InventoryRepository,
        products: ProductDirectory,
        transaction_manager: TransactionManager,
    ) -> None:
        self._repository = repository
        self._products = products
        self._transaction_manager = transaction_manager

    def execute(
        self,
        household_id: int,
        product_id: int,
        amount: Decimal,
        unit: MeasurementUnit,
    ) -> InventoryItemSnapshot:
        if not self._products.is_household_product(household_id, product_id):
            raise ProductNotFoundError
        with self._transaction_manager.atomic():
            existing = self._repository.lock_item_by_product(product_id)
            if existing is None:
                raise InventoryItemNotFoundError
            remaining = existing.as_quantity().subtract(Quantity(amount=amount, unit=unit))
            floored = remaining.amount if remaining.amount > EMPTY else EMPTY
            return self._repository.set_quantity(existing.id, floored)
