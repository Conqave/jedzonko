from decimal import Decimal

from catalog.domain.measurement import MeasurementDimension
from catalog.domain.measurement import MeasurementUnit as UnitValue
from catalog.models import Ingredient, MeasurementUnit
from inventory.application.errors import (
    IngredientNotFoundError,
    InventoryItemNotFoundError,
    MeasurementUnitNotFoundError,
)
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot
from inventory.models import InventoryItem


class DjangoInventoryRepository(InventoryRepository):
    def list_items(self, household_id: int) -> list[InventoryItemSnapshot]:
        rows = InventoryItem.objects.filter(household_id=household_id).select_related(
            "ingredient", "unit", "category"
        )
        return [self._to_snapshot(row) for row in rows]

    def find_item(self, item_id: int) -> InventoryItemSnapshot | None:
        row = (
            InventoryItem.objects.filter(pk=item_id)
            .select_related("ingredient", "unit", "category")
            .first()
        )
        return None if row is None else self._to_snapshot(row)

    def find_household_id_for_item(self, item_id: int) -> int | None:
        row = (
            InventoryItem.objects.filter(pk=item_id).values_list("household_id", flat=True).first()
        )
        return None if row is None else int(row)

    def find_item_by_ingredient(
        self, household_id: int, ingredient_id: int
    ) -> InventoryItemSnapshot | None:
        row = (
            InventoryItem.objects.filter(household_id=household_id, ingredient_id=ingredient_id)
            .select_related("ingredient", "unit", "category")
            .first()
        )
        return None if row is None else self._to_snapshot(row)

    def lock_item_by_ingredient(
        self, household_id: int, ingredient_id: int
    ) -> InventoryItemSnapshot | None:
        row = (
            InventoryItem.objects.select_for_update()
            .filter(household_id=household_id, ingredient_id=ingredient_id)
            .first()
        )
        if row is None:
            return None
        return self._to_snapshot(
            InventoryItem.objects.select_related("ingredient", "unit", "category").get(pk=row.pk)
        )

    def create_item(
        self,
        household_id: int,
        ingredient_id: int,
        quantity: Decimal,
        unit_code: str,
        minimum_quantity: Decimal | None,
        category_id: int | None,
    ) -> InventoryItemSnapshot:
        if not Ingredient.objects.filter(pk=ingredient_id).exists():
            raise IngredientNotFoundError
        unit = MeasurementUnit.objects.filter(code=unit_code).first()
        if unit is None:
            raise MeasurementUnitNotFoundError
        item = InventoryItem.objects.create(
            household_id=household_id,
            ingredient_id=ingredient_id,
            unit=unit,
            quantity=quantity,
            minimum_quantity=minimum_quantity,
            category_id=category_id,
        )
        return self._to_snapshot(
            InventoryItem.objects.select_related("ingredient", "unit", "category").get(pk=item.pk)
        )

    def set_quantity(self, item_id: int, quantity: Decimal) -> InventoryItemSnapshot:
        updated = InventoryItem.objects.filter(pk=item_id).update(quantity=quantity)
        if updated == 0:
            raise InventoryItemNotFoundError
        row = InventoryItem.objects.select_related("ingredient", "unit", "category").get(pk=item_id)
        return self._to_snapshot(row)

    def delete_item(self, item_id: int) -> None:
        deleted, _ = InventoryItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise InventoryItemNotFoundError

    @staticmethod
    def _to_snapshot(row: InventoryItem) -> InventoryItemSnapshot:
        return InventoryItemSnapshot(
            id=row.pk,
            ingredient_id=row.ingredient_id,
            ingredient_name=row.ingredient.name,
            quantity=row.quantity,
            unit=UnitValue(
                code=row.unit.code,
                dimension=MeasurementDimension(row.unit.dimension),
                factor_to_base=row.unit.factor_to_base,
            ),
            minimum_quantity=row.minimum_quantity,
            category_name=None if row.category is None else row.category.name,
            photo_url=row.photo.url if row.photo else None,
        )
