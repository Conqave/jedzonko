from datetime import datetime
from decimal import Decimal

from django.db.models import Count, Exists, OuterRef
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
from shopping.models import (
    PrimaryShoppingList,
    PurchasedShoppingItem,
    ShoppingList,
    ShoppingListItem,
)

PRIMARY_LIST_NAME = "Lista zakupów"


class DjangoShoppingListRepository(ShoppingListRepository):
    def list_lists(self, household_id: int) -> list[ShoppingListSummary]:
        rows = (
            ShoppingList.objects.filter(household_id=household_id)
            .annotate(
                pending_total=Count("items", distinct=True),
                purchased_total=Count("purchased_items", distinct=True),
                primary_marker_exists=Exists(
                    PrimaryShoppingList.objects.filter(shopping_list_id=OuterRef("pk"))
                ),
            )
            .values("id", "name", "primary_marker_exists", "pending_total", "purchased_total")
        )
        summaries = [
            ShoppingListSummary(
                id=int(row["id"]),
                name=str(row["name"]),
                is_primary=bool(row["primary_marker_exists"]),
                item_count=int(row["pending_total"]) + int(row["purchased_total"]),
            )
            for row in rows
        ]
        return sorted(summaries, key=lambda summary: (not summary.is_primary, summary.name))

    def get_or_create_primary_list(self, household_id: int) -> ShoppingListSummary:
        marker = (
            PrimaryShoppingList.objects.filter(household_id=household_id)
            .select_related("shopping_list")
            .first()
        )
        if marker is not None:
            return self._to_list_summary(marker.shopping_list, True)
        shopping_list = ShoppingList.objects.create(
            household_id=household_id, name=PRIMARY_LIST_NAME
        )
        PrimaryShoppingList.objects.create(household_id=household_id, shopping_list=shopping_list)
        return self._to_list_summary(shopping_list, True)

    def create_list(self, household_id: int, name: str) -> ShoppingListSummary:
        row = ShoppingList.objects.create(household_id=household_id, name=name)
        return self._to_list_summary(row, False)

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
        ordered: list[tuple[datetime, int, ShoppingItemSnapshot]] = []
        for row in ShoppingListItem.objects.filter(shopping_list_id=list_id).select_related(
            "ingredient", "unit"
        ):
            ordered.append((row.created_at, row.pk, self._to_item_snapshot(row)))
        for purchased in PurchasedShoppingItem.objects.filter(
            shopping_list_id=list_id
        ).select_related("ingredient", "unit"):
            ordered.append(
                (purchased.created_at, purchased.pk, self._to_purchased_snapshot(purchased))
            )
        return [entry[2] for entry in sorted(ordered, key=lambda entry: (entry[0], entry[1]))]

    def list_pending_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        rows = ShoppingListItem.objects.filter(shopping_list_id=list_id).select_related(
            "ingredient", "unit"
        )
        return [self._to_item_snapshot(row) for row in rows]

    def find_pending_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        row = (
            ShoppingListItem.objects.filter(pk=item_id).select_related("ingredient", "unit").first()
        )
        return None if row is None else self._to_item_snapshot(row)

    def find_pending_item_by_ingredient(
        self, list_id: int, ingredient_id: int
    ) -> ShoppingItemSnapshot | None:
        row = (
            ShoppingListItem.objects.filter(shopping_list_id=list_id, ingredient_id=ingredient_id)
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

    def purchase_item(self, item_id: int) -> ShoppingItemSnapshot:
        row = (
            ShoppingListItem.objects.filter(pk=item_id).select_related("ingredient", "unit").first()
        )
        if row is None:
            raise ShoppingListItemNotFoundError
        deleted, _ = ShoppingListItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise ShoppingListItemNotFoundError
        purchased = PurchasedShoppingItem.objects.create(
            shopping_list_id=row.shopping_list_id,
            ingredient_id=row.ingredient_id,
            free_text=row.free_text,
            unit_id=row.unit_id,
            quantity=row.quantity,
            created_at=row.created_at,
            purchased_at=timezone.now(),
        )
        return self._to_purchased_snapshot(
            PurchasedShoppingItem.objects.select_related("ingredient", "unit").get(pk=purchased.pk)
        )

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
    def _to_unit_value(unit: MeasurementUnit | None) -> UnitValue | None:
        if unit is None:
            return None
        return UnitValue(
            code=unit.code,
            dimension=MeasurementDimension(unit.dimension),
            factor_to_base=unit.factor_to_base,
        )

    @staticmethod
    def _to_list_summary(row: ShoppingList, is_primary: bool) -> ShoppingListSummary:
        return ShoppingListSummary(
            id=row.pk,
            name=row.name,
            is_primary=is_primary,
            item_count=row.items.count() + row.purchased_items.count(),
        )

    @classmethod
    def _to_item_snapshot(cls, row: ShoppingListItem) -> ShoppingItemSnapshot:
        return ShoppingItemSnapshot(
            id=row.pk,
            ingredient_id=row.ingredient_id,
            ingredient_name=None if row.ingredient is None else row.ingredient.name,
            free_text=row.free_text,
            quantity=row.quantity,
            unit=cls._to_unit_value(row.unit),
            is_purchased=False,
        )

    @classmethod
    def _to_purchased_snapshot(cls, row: PurchasedShoppingItem) -> ShoppingItemSnapshot:
        return ShoppingItemSnapshot(
            id=row.pk,
            ingredient_id=row.ingredient_id,
            ingredient_name=None if row.ingredient is None else row.ingredient.name,
            free_text=row.free_text,
            quantity=row.quantity,
            unit=cls._to_unit_value(row.unit),
            is_purchased=True,
        )
