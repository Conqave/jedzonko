from decimal import Decimal

from inventory.application.errors import (
    InventoryItemNotFoundError,
    MeasurementUnitNotFoundError,
)
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.product_renamer import ProductRenamer
from inventory.domain.models import InventoryItemSnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.measurement_units import find_measurement_unit
from shared.transactions import TransactionManager


class UpdateInventoryItem:
    def __init__(
        self,
        repository: InventoryRepository,
        product_renamer: ProductRenamer,
        transactions: TransactionManager,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._product_renamer = product_renamer
        self._transactions = transactions
        self._memberships = memberships

    def execute(
        self,
        user_id: int,
        item_id: int,
        product_name: str | None,
        quantity: Decimal | None,
        unit_code: str | None,
    ) -> InventoryItemSnapshot:
        item = self._repository.find_item(item_id)
        if item is None:
            raise InventoryItemNotFoundError
        require_membership(self._memberships, user_id, item.household_id)
        if unit_code is not None and find_measurement_unit(unit_code) is None:
            raise MeasurementUnitNotFoundError
        with self._transactions.atomic():
            if product_name is not None:
                self._product_renamer.set_product_name(user_id, item.product_id, product_name)
            return self._repository.update_item(item_id, quantity, unit_code)
