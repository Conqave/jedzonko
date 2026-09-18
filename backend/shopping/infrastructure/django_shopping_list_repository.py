from decimal import Decimal

from django.db.models import Count
from django.utils import timezone

from catalog.domain.measurement import MeasurementDimension
from catalog.domain.measurement import MeasurementUnit as UnitValue
from catalog.models import MeasurementUnit
from shopping.application.errors import (
    InvalidShoppingItemError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_list_summary import ShoppingListSummary
from shopping.models import ShoppingList, ShoppingListItem

PRIMARY_LIST_NAME = "Lista zakupów"


class DjangoShoppingListRepository(ShoppingListRepository):
    def list_lists(self, household_id: int) -> list[ShoppingListSummary]:
        rows = (
            ShoppingList.objects.filter(household_id=household_id)
            .annotate(item_total=Count("items"))
            .values("id", "name", "is_primary", "item_total")
        )
        return [
            ShoppingListSummary(
                id=int(row["id"]),
                name=str(row["name"]),
                is_primary=bool(row["is_primary"]),
                item_count=int(row["item_total"]),
            )
            for row in rows
        ]

    def get_or_create_primary_list(self, household_id: int) -> ShoppingListSummary:
        row, _ = ShoppingList.objects.get_or_create(
            household_id=household_id, is_primary=True, defaults={"name": PRIMARY_LIST_NAME}
        )
        return self._to_list_summary(row)

    def create_list(self, household_id: int, name: str) -> ShoppingListSummary:
        row = ShoppingList.objects.create(household_id=household_id, name=name, is_primary=False)
        return self._to_list_summary(row)

    def find_household_id_for_list(self, list_id: int) -> int | None:
        row = ShoppingList.objects.filter(pk=list_id).values_list("household_id", flat=True).first()
        return None if row is None else int(row)

    def find_household_id_for_item(self, item_id: int) -> int | None:
        row = (
            ShoppingListItem.objects.filter(pk=item_id)
            .values_list("shopping_list__household_id", flat=True)
            .first()
        )
        return None if row is None else int(row)

    def list_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        rows = ShoppingListItem.objects.filter(shopping_list_id=list_id).select_related(
            "ingredient", "unit"
        )
        return [self._to_item_snapshot(row) for row in rows]

    def list_unpurchased_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        rows = ShoppingListItem.objects.filter(
            shopping_list_id=list_id, is_purchased=False
        ).select_related("ingredient", "unit")
        return [self._to_item_snapshot(row) for row in rows]

    def find_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        row = (
            ShoppingListItem.objects.filter(pk=item_id).select_related("ingredient", "unit").first()
        )
        return None if row is None else self._to_item_snapshot(row)

    def find_unpurchased_item_by_ingredient(
        self, list_id: int, ingredient_id: int
    ) -> ShoppingItemSnapshot | None:
        row = (
            ShoppingListItem.objects.filter(
                shopping_list_id=list_id, ingredient_id=ingredient_id, is_purchased=False
            )
            .select_related("ingredient", "unit")
            .first()
        )
        return None if row is None else self._to_item_snapshot(row)

    def add_item(
        self,
        list_id: int,
        ingredient_id: int | None,
        free_text: str | None,
        quantity: Decimal,
        unit_code: str | None,
    ) -> ShoppingItemSnapshot:
        if not ShoppingList.objects.filter(pk=list_id).exists():
            raise ShoppingListNotFoundError
        item = ShoppingListItem.objects.create(
            shopping_list_id=list_id,
            ingredient_id=ingredient_id,
            free_text=free_text,
            unit=self._find_unit(unit_code),
            quantity=quantity,
        )
        return self._read_item(item.pk)

    def set_item_quantity(
        self, item_id: int, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        updated = ShoppingListItem.objects.filter(pk=item_id).update(
            quantity=quantity, unit=self._find_unit(unit_code)
        )
        if updated == 0:
            raise ShoppingListItemNotFoundError
        return self._read_item(item_id)

    def mark_purchased(self, item_id: int) -> ShoppingItemSnapshot:
        updated = ShoppingListItem.objects.filter(pk=item_id, is_purchased=False).update(
            is_purchased=True, purchased_at=timezone.now()
        )
        if updated == 0:
            raise ShoppingListItemNotFoundError
        return self._read_item(item_id)

    def delete_item(self, item_id: int) -> None:
        deleted, _ = ShoppingListItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise ShoppingListItemNotFoundError

    def _read_item(self, item_id: int) -> ShoppingItemSnapshot:
        row = ShoppingListItem.objects.select_related("ingredient", "unit").get(pk=item_id)
        return self._to_item_snapshot(row)

    @staticmethod
    def _find_unit(unit_code: str | None) -> MeasurementUnit | None:
        if unit_code is None:
            return None
        unit = MeasurementUnit.objects.filter(code=unit_code).first()
        if unit is None:
            raise InvalidShoppingItemError
        return unit

    @staticmethod
    def _to_list_summary(row: ShoppingList) -> ShoppingListSummary:
        return ShoppingListSummary(
            id=row.pk,
            name=row.name,
            is_primary=row.is_primary,
            item_count=row.items.count(),
        )

    @staticmethod
    def _to_item_snapshot(row: ShoppingListItem) -> ShoppingItemSnapshot:
        unit = (
            None
            if row.unit is None
            else UnitValue(
                code=row.unit.code,
                dimension=MeasurementDimension(row.unit.dimension),
                factor_to_base=row.unit.factor_to_base,
            )
        )
        return ShoppingItemSnapshot(
            id=row.pk,
            ingredient_id=row.ingredient_id,
            ingredient_name=None if row.ingredient is None else row.ingredient.name,
            free_text=row.free_text,
            quantity=row.quantity,
            unit=unit,
            is_purchased=row.is_purchased,
        )
