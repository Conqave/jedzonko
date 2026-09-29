from decimal import Decimal

from inventory.application.errors import ProductNotFoundError
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.product_directory import ProductDirectory
from inventory.domain.models import InventoryItemSnapshot
from shared.measurement import MeasurementUnit, Quantity
from shared.transactions import TransactionManager


class AddQuantityToInventory:
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
                return self._repository.create_item(product_id, amount, unit.code, None)
            increased = existing.as_quantity().add(Quantity(amount=amount, unit=unit))
            return self._repository.set_quantity(existing.id, increased.amount)
