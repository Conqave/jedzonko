from datetime import datetime
from decimal import Decimal

from django.db.models import Count, QuerySet

from shared.measurement import MeasurementUnit
from shared.measurement_units import find_measurement_unit
from shopping.application.errors import (
    InvalidShoppingItemError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_item_status import ShoppingItemStatus
from shopping.domain.shopping_list_summary import ShoppingListSummary
from shopping.domain.shopping_subject import ShoppingSubject
from shopping.models import ShoppingList, ShoppingListItem

PENDING = ShoppingItemStatus.PENDING.value
PURCHASED = ShoppingItemStatus.PURCHASED.value


class DjangoShoppingListRepository(ShoppingListRepository):
    def list_lists(self, household_id: int) -> list[ShoppingListSummary]:
        rows = ShoppingList.objects.filter(household_id=household_id).annotate(
            item_total=Count("items")
        )
        return [_to_list(row, row.item_total) for row in rows]

    def find_list(self, list_id: int) -> ShoppingListSummary | None:
        row = ShoppingList.objects.filter(pk=list_id).annotate(item_total=Count("items")).first()
        return None if row is None else _to_list(row, row.item_total)

    def find_primary_list(self, household_id: int) -> ShoppingListSummary | None:
        row = (
            ShoppingList.objects.filter(household_id=household_id, is_primary=True)
            .annotate(item_total=Count("items"))
            .first()
        )
        return None if row is None else _to_list(row, row.item_total)

    def create_list(self, household_id: int, name: str, is_primary: bool) -> ShoppingListSummary:
        row = ShoppingList.objects.create(
            household_id=household_id, name=name, is_primary=is_primary
        )
        return _to_list(row, 0)

    def rename_list(self, list_id: int, name: str) -> ShoppingListSummary:
        if ShoppingList.objects.filter(pk=list_id).update(name=name) == 0:
            raise ShoppingListNotFoundError
        renamed = self.find_list(list_id)
        if renamed is None:
            raise ShoppingListNotFoundError
        return renamed

    def delete_list(self, list_id: int) -> None:
        deleted, _ = ShoppingList.objects.filter(pk=list_id).delete()
        if deleted == 0:
            raise ShoppingListNotFoundError

    def find_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        row = _items().filter(pk=item_id).first()
        return None if row is None else _to_item(row)

    def list_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        return [_to_item(row) for row in _items().filter(shopping_list_id=list_id)]

    def list_pending_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        rows = _items().filter(shopping_list_id=list_id, status=PENDING)
        return [_to_item(row) for row in rows]

    def find_pending_item(
        self, list_id: int, subject: ShoppingSubject
    ) -> ShoppingItemSnapshot | None:
        rows = _items().filter(shopping_list_id=list_id, status=PENDING)
        if subject.product_id is not None:
            rows = rows.filter(product_id=subject.product_id)
        elif subject.ingredient_id is not None:
            rows = rows.filter(ingredient_id=subject.ingredient_id)
        else:
            rows = rows.filter(free_text=subject.free_text)
        row = rows.first()
        return None if row is None else _to_item(row)

    def add_item(
        self, list_id: int, subject: ShoppingSubject, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        row = ShoppingListItem.objects.create(
            shopping_list_id=list_id,
            product_id=subject.product_id,
            ingredient_id=subject.ingredient_id,
            free_text=subject.free_text,
            unit_code=unit_code,
            quantity=quantity,
            status=PENDING,
        )
        return self._read(row.pk)

    def set_item_quantity(
        self, item_id: int, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        updated = ShoppingListItem.objects.filter(pk=item_id).update(
            quantity=quantity, unit_code=unit_code
        )
        if updated == 0:
            raise ShoppingListItemNotFoundError
        return self._read(item_id)

    def mark_purchased(self, item_id: int, purchased_at: datetime) -> ShoppingItemSnapshot:
        updated = ShoppingListItem.objects.filter(pk=item_id, status=PENDING).update(
            status=PURCHASED, purchased_at=purchased_at
        )
        if updated == 0:
            raise ShoppingListItemNotFoundError
        return self._read(item_id)

    def mark_pending(self, item_id: int) -> ShoppingItemSnapshot:
        updated = ShoppingListItem.objects.filter(pk=item_id, status=PURCHASED).update(
            status=PENDING, purchased_at=None
        )
        if updated == 0:
            raise ShoppingListItemNotFoundError
        return self._read(item_id)

    def delete_item(self, item_id: int) -> None:
        deleted, _ = ShoppingListItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise ShoppingListItemNotFoundError

    def list_items_about_ingredient(self, ingredient_id: int) -> list[ShoppingItemSnapshot]:
        return [_to_item(row) for row in _items().filter(ingredient_id=ingredient_id)]

    def set_item_product(self, item_id: int, product_id: int) -> ShoppingItemSnapshot:
        updated = ShoppingListItem.objects.filter(pk=item_id).update(
            product_id=product_id, ingredient_id=None, free_text=None
        )
        if updated == 0:
            raise ShoppingListItemNotFoundError
        return self._read(item_id)

    def set_item_ingredient(self, item_id: int, ingredient_id: int) -> None:
        if ShoppingListItem.objects.filter(pk=item_id).update(ingredient_id=ingredient_id) == 0:
            raise ShoppingListItemNotFoundError

    @staticmethod
    def _read(item_id: int) -> ShoppingItemSnapshot:
        row = _items().get(pk=item_id)
        return _to_item(row)


def _items() -> QuerySet[ShoppingListItem]:
    return ShoppingListItem.objects.select_related("product", "ingredient")


def _to_list(row: ShoppingList, item_count: int) -> ShoppingListSummary:
    return ShoppingListSummary(
        id=row.pk,
        household_id=row.household_id,
        name=row.name,
        is_primary=row.is_primary,
        item_count=item_count,
    )


def _to_item(row: ShoppingListItem) -> ShoppingItemSnapshot:
    subject = ShoppingSubject(
        product_id=row.product_id, ingredient_id=row.ingredient_id, free_text=row.free_text
    )
    if row.product is not None:
        name = row.product.name
    elif row.ingredient is not None:
        name = row.ingredient.name
    elif row.free_text is not None:
        name = row.free_text
    else:
        raise AssertionError("A shopping item without a subject.")
    unit = _to_unit(row.unit_code)
    status = ShoppingItemStatus(row.status)
    return ShoppingItemSnapshot(
        id=row.pk,
        list_id=row.shopping_list_id,
        subject=subject,
        name=name,
        quantity=row.quantity,
        unit=unit,
        status=status,
        purchased_at=row.purchased_at,
    )


def _to_unit(unit_code: str | None) -> MeasurementUnit | None:
    if unit_code is None:
        return None
    unit = find_measurement_unit(unit_code)
    if unit is None:
        raise InvalidShoppingItemError
    return unit
