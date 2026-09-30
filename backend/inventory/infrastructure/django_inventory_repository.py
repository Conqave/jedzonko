from decimal import Decimal

from django.core.files.base import ContentFile
from django.db.models import QuerySet

from inventory.application.errors import (
    InventoryItemNotFoundError,
    InventoryPhotoNotFoundError,
    MeasurementUnitNotFoundError,
)
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot
from inventory.domain.photo import InventoryPhoto
from inventory.models import InventoryItem
from shared.measurement import MeasurementUnit
from shared.measurement_units import find_measurement_unit


class DjangoInventoryRepository(InventoryRepository):
    def list_items(self, household_id: int) -> list[InventoryItemSnapshot]:
        rows = _items_with_product().filter(product__household_id=household_id)
        return [self._to_snapshot(row) for row in rows]

    def find_item(self, item_id: int) -> InventoryItemSnapshot | None:
        row = _items_with_product().filter(pk=item_id).first()
        return None if row is None else self._to_snapshot(row)

    def find_household_id_for_item(self, item_id: int) -> int | None:
        row = (
            InventoryItem.objects.filter(pk=item_id)
            .values_list("product__household_id", flat=True)
            .first()
        )
        return None if row is None else int(row)

    def find_item_by_product(self, product_id: int) -> InventoryItemSnapshot | None:
        row = _items_with_product().filter(product_id=product_id).first()
        return None if row is None else self._to_snapshot(row)

    def lock_item_by_product(self, product_id: int) -> InventoryItemSnapshot | None:
        row = InventoryItem.objects.select_for_update().filter(product_id=product_id).first()
        if row is None:
            return None
        return self._load_snapshot(row.pk)

    def create_item(
        self,
        product_id: int,
        quantity: Decimal,
        unit_code: str,
        minimum_quantity: Decimal | None,
    ) -> InventoryItemSnapshot:
        item = InventoryItem.objects.create(
            product_id=product_id,
            unit_code=unit_code,
            quantity=quantity,
            minimum_quantity=minimum_quantity,
        )
        return self._load_snapshot(item.pk)

    def set_quantity(self, item_id: int, quantity: Decimal) -> InventoryItemSnapshot:
        updated = InventoryItem.objects.filter(pk=item_id).update(quantity=quantity)
        if updated == 0:
            raise InventoryItemNotFoundError
        return self._load_snapshot(item_id)

    def update_item(
        self, item_id: int, quantity: Decimal | None, unit_code: str | None
    ) -> InventoryItemSnapshot:
        changes: dict[str, Decimal | str] = {}
        if quantity is not None:
            changes["quantity"] = quantity
        if unit_code is not None:
            changes["unit_code"] = unit_code
        if changes:
            updated = InventoryItem.objects.filter(pk=item_id).update(**changes)
            if updated == 0:
                raise InventoryItemNotFoundError
        return self._load_snapshot(item_id)

    def set_minimum_quantity(
        self, item_id: int, minimum_quantity: Decimal | None
    ) -> InventoryItemSnapshot:
        updated = InventoryItem.objects.filter(pk=item_id).update(minimum_quantity=minimum_quantity)
        if updated == 0:
            raise InventoryItemNotFoundError
        return self._load_snapshot(item_id)

    def set_photo(self, item_id: int, photo: InventoryPhoto) -> InventoryItemSnapshot:
        row = self._get_row(item_id)
        if row.photo:
            row.photo.delete(save=False)
        row.photo.save(photo.filename, ContentFile(photo.content), save=True)
        return self._to_snapshot(row)

    def clear_photo(self, item_id: int) -> InventoryItemSnapshot:
        row = self._get_row(item_id)
        if not row.photo:
            raise InventoryPhotoNotFoundError
        row.photo.delete(save=True)
        return self._to_snapshot(row)

    def delete_item(self, item_id: int) -> None:
        deleted, _ = InventoryItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise InventoryItemNotFoundError

    @staticmethod
    def _get_row(item_id: int) -> InventoryItem:
        row = _items_with_product().filter(pk=item_id).first()
        if row is None:
            raise InventoryItemNotFoundError
        return row

    @classmethod
    def _load_snapshot(cls, item_id: int) -> InventoryItemSnapshot:
        row = cls._get_row(item_id)
        return cls._to_snapshot(row)

    @classmethod
    def _to_snapshot(cls, row: InventoryItem) -> InventoryItemSnapshot:
        unit = cls._to_unit(row.unit_code)
        return InventoryItemSnapshot(
            id=row.pk,
            product_id=row.product_id,
            household_id=row.product.household_id,
            product_name=row.product.name,
            quantity=row.quantity,
            unit=unit,
            minimum_quantity=row.minimum_quantity,
            photo_url=row.photo.url if row.photo else None,
        )

    @staticmethod
    def _to_unit(unit_code: str) -> MeasurementUnit:
        unit = find_measurement_unit(unit_code)
        if unit is None:
            raise MeasurementUnitNotFoundError
        return unit


def _items_with_product() -> QuerySet[InventoryItem]:
    return InventoryItem.objects.select_related("product")
