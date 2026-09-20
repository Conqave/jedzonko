from decimal import Decimal

from django.core.files.base import ContentFile

from households.models import Product
from inventory.application.errors import (
    InventoryItemNotFoundError,
    InventoryPhotoNotFoundError,
    MeasurementUnitNotFoundError,
    ProductNotFoundError,
)
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot
from inventory.domain.photo import InventoryPhoto
from inventory.models import InventoryItem
from shared.measurement import MeasurementUnit
from shared.measurement_units import find_measurement_unit


class DjangoInventoryRepository(InventoryRepository):
    def list_items(self, household_id: int) -> list[InventoryItemSnapshot]:
        rows = (
            InventoryItem.objects.filter(household_id=household_id)
            .select_related("product", "category")
            .prefetch_related("product__aliases")
        )
        return [self._to_snapshot(row) for row in rows]

    def find_item(self, item_id: int) -> InventoryItemSnapshot | None:
        row = InventoryItem.objects.filter(pk=item_id).select_related("product", "category").first()
        return None if row is None else self._to_snapshot(row)

    def find_household_id_for_item(self, item_id: int) -> int | None:
        row = (
            InventoryItem.objects.filter(pk=item_id).values_list("household_id", flat=True).first()
        )
        return None if row is None else int(row)

    def find_item_by_product(
        self, household_id: int, product_id: int
    ) -> InventoryItemSnapshot | None:
        row = (
            InventoryItem.objects.filter(household_id=household_id, product_id=product_id)
            .select_related("product", "category")
            .first()
        )
        return None if row is None else self._to_snapshot(row)

    def lock_item_by_product(
        self, household_id: int, product_id: int
    ) -> InventoryItemSnapshot | None:
        row = (
            InventoryItem.objects.select_for_update()
            .filter(household_id=household_id, product_id=product_id)
            .first()
        )
        if row is None:
            return None
        return self._to_snapshot(
            InventoryItem.objects.select_related("product", "category").get(pk=row.pk)
        )

    def create_item(
        self,
        household_id: int,
        product_id: int,
        quantity: Decimal,
        unit_code: str,
        minimum_quantity: Decimal | None,
        category_id: int | None,
    ) -> InventoryItemSnapshot:
        if not Product.objects.filter(pk=product_id, household_id=household_id).exists():
            raise ProductNotFoundError
        if find_measurement_unit(unit_code) is None:
            raise MeasurementUnitNotFoundError
        item = InventoryItem.objects.create(
            household_id=household_id,
            product_id=product_id,
            unit_code=unit_code,
            quantity=quantity,
            minimum_quantity=minimum_quantity,
            category_id=category_id,
        )
        return self._to_snapshot(
            InventoryItem.objects.select_related("product", "category").get(pk=item.pk)
        )

    def set_quantity(self, item_id: int, quantity: Decimal) -> InventoryItemSnapshot:
        updated = InventoryItem.objects.filter(pk=item_id).update(quantity=quantity)
        if updated == 0:
            raise InventoryItemNotFoundError
        row = InventoryItem.objects.select_related("product", "category").get(pk=item_id)
        return self._to_snapshot(row)

    def update_item(
        self, item_id: int, quantity: Decimal | None, unit_code: str | None
    ) -> InventoryItemSnapshot:
        changes: dict[str, Decimal | str] = {}
        if quantity is not None:
            changes["quantity"] = quantity
        if unit_code is not None:
            if find_measurement_unit(unit_code) is None:
                raise MeasurementUnitNotFoundError
            changes["unit_code"] = unit_code
        if changes:
            updated = InventoryItem.objects.filter(pk=item_id).update(**changes)
            if updated == 0:
                raise InventoryItemNotFoundError
        row = InventoryItem.objects.select_related("product", "category").filter(pk=item_id).first()
        if row is None:
            raise InventoryItemNotFoundError
        return self._to_snapshot(row)

    def set_category(self, item_id: int, category_id: int | None) -> InventoryItemSnapshot:
        updated = InventoryItem.objects.filter(pk=item_id).update(category_id=category_id)
        if updated == 0:
            raise InventoryItemNotFoundError
        row = InventoryItem.objects.select_related("product", "category").get(pk=item_id)
        return self._to_snapshot(row)

    def set_photo(self, item_id: int, photo: InventoryPhoto) -> InventoryItemSnapshot:
        row = InventoryItem.objects.select_related("product", "category").filter(pk=item_id).first()
        if row is None:
            raise InventoryItemNotFoundError
        if row.photo:
            row.photo.delete(save=False)
        row.photo.save(photo.filename, ContentFile(photo.content), save=True)
        return self._to_snapshot(row)

    def clear_photo(self, item_id: int) -> InventoryItemSnapshot:
        row = InventoryItem.objects.select_related("product", "category").filter(pk=item_id).first()
        if row is None:
            raise InventoryItemNotFoundError
        if not row.photo:
            raise InventoryPhotoNotFoundError
        row.photo.delete(save=True)
        return self._to_snapshot(row)

    def delete_item(self, item_id: int) -> None:
        deleted, _ = InventoryItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise InventoryItemNotFoundError

    @classmethod
    def _to_snapshot(cls, row: InventoryItem) -> InventoryItemSnapshot:
        return InventoryItemSnapshot(
            id=row.pk,
            product_id=row.product_id,
            product_name=row.product.name,
            normalized_name=row.product.normalized_name,
            alias_names=tuple(alias.normalized_name for alias in row.product.aliases.all()),
            quantity=row.quantity,
            unit=cls._to_unit(row.unit_code),
            package_quantity=row.product.package_quantity,
            package_unit=cls._to_package_unit(row.product.package_unit_code),
            minimum_quantity=row.minimum_quantity,
            category_id=row.category_id,
            category_name=None if row.category is None else row.category.name,
            photo_url=row.photo.url if row.photo else None,
        )

    @staticmethod
    def _to_package_unit(unit_code: str) -> MeasurementUnit | None:
        if not unit_code:
            return None
        unit = find_measurement_unit(unit_code)
        if unit is None:
            raise MeasurementUnitNotFoundError
        return unit

    @staticmethod
    def _to_unit(unit_code: str) -> MeasurementUnit:
        unit = find_measurement_unit(unit_code)
        if unit is None:
            raise MeasurementUnitNotFoundError
        return unit
