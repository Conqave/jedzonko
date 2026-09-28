from datetime import datetime
from decimal import Decimal

from django.db.models import Count, Exists, OuterRef
from django.utils import timezone

from shared.measurement import MeasurementUnit
from shared.measurement_units import find_measurement_unit
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
from households.models import IngredientTag
from shared.text import normalize_text

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
            "product"
        ):
            ordered.append((row.created_at, row.pk, self._to_item_snapshot(row)))
        for purchased in PurchasedShoppingItem.objects.filter(
            shopping_list_id=list_id
        ).select_related("product"):
            ordered.append(
                (purchased.created_at, purchased.pk, self._to_purchased_snapshot(purchased))
            )
        return [entry[2] for entry in sorted(ordered, key=lambda entry: (entry[0], entry[1]))]

    def list_pending_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        rows = ShoppingListItem.objects.filter(shopping_list_id=list_id).select_related("product")
        return [self._to_item_snapshot(row) for row in rows]

    def find_pending_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        row = ShoppingListItem.objects.filter(pk=item_id).select_related("product").first()
        return None if row is None else self._to_item_snapshot(row)

    def find_pending_item_by_product(
        self, list_id: int, product_id: int
    ) -> ShoppingItemSnapshot | None:
        row = (
            ShoppingListItem.objects.filter(shopping_list_id=list_id, product_id=product_id)
            .select_related("product")
            .first()
        )
        return None if row is None else self._to_item_snapshot(row)

    def add_item(
        self,
        list_id: int,
        product_id: int | None,
        free_text: str | None,
        quantity: Decimal,
        unit_code: str | None,
    ) -> ShoppingItemSnapshot:
        if not ShoppingList.objects.filter(pk=list_id).exists():
            raise ShoppingListNotFoundError
        item = ShoppingListItem.objects.create(
            shopping_list_id=list_id,
            product_id=product_id,
            free_text=free_text,
            unit_code=self._validated_unit_code(unit_code),
            quantity=quantity,
        )
        return self._read_item(item.pk)

    def set_item_quantity(
        self, item_id: int, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        updated = ShoppingListItem.objects.filter(pk=item_id).update(
            quantity=quantity, unit_code=self._validated_unit_code(unit_code)
        )
        if updated == 0:
            raise ShoppingListItemNotFoundError
        return self._read_item(item_id)

    def purchase_item(self, item_id: int) -> ShoppingItemSnapshot:
        row = ShoppingListItem.objects.filter(pk=item_id).select_related("product").first()
        if row is None:
            raise ShoppingListItemNotFoundError
        deleted, _ = ShoppingListItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise ShoppingListItemNotFoundError
        purchased = PurchasedShoppingItem.objects.create(
            shopping_list_id=row.shopping_list_id,
            product_id=row.product_id,
            free_text=row.free_text,
            unit_code=row.unit_code,
            quantity=row.quantity,
            created_at=row.created_at,
            purchased_at=timezone.now(),
        )
        return self._to_purchased_snapshot(
            PurchasedShoppingItem.objects.select_related("product").get(pk=purchased.pk)
        )

    def delete_item(self, item_id: int) -> None:
        deleted, _ = ShoppingListItem.objects.filter(pk=item_id).delete()
        if deleted == 0:
            raise ShoppingListItemNotFoundError

    def _read_item(self, item_id: int) -> ShoppingItemSnapshot:
        row = ShoppingListItem.objects.select_related("product").get(pk=item_id)
        return self._to_item_snapshot(row)

    @staticmethod
    def _validated_unit_code(unit_code: str | None) -> str | None:
        if unit_code is None:
            return None
        if find_measurement_unit(unit_code) is None:
            raise InvalidShoppingItemError
        return unit_code

    @staticmethod
    def _to_unit_value(unit_code: str | None) -> MeasurementUnit | None:
        if unit_code is None:
            return None
        unit = find_measurement_unit(unit_code)
        if unit is None:
            raise InvalidShoppingItemError
        return unit

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
            product_id=row.product_id,
            product_name=None if row.product is None else row.product.name,
            free_text=row.free_text,
            quantity=row.quantity,
            unit=cls._to_unit_value(row.unit_code),
            is_purchased=False,
            tag_names=cls._tag_names(row.product, row.free_text, row.shopping_list.household_id),
        )

    @classmethod
    def _to_purchased_snapshot(cls, row: PurchasedShoppingItem) -> ShoppingItemSnapshot:
        return ShoppingItemSnapshot(
            id=row.pk,
            product_id=row.product_id,
            product_name=None if row.product is None else row.product.name,
            free_text=row.free_text,
            quantity=row.quantity,
            unit=cls._to_unit_value(row.unit_code),
            is_purchased=True,
            tag_names=cls._tag_names(row.product, row.free_text, row.shopping_list.household_id),
        )

    @staticmethod
    def _tag_names(product: object, free_text: str | None, household_id: int) -> tuple[str, ...]:
        if product is not None:
            return tuple(product.ingredient_tags.values_list("name", flat=True))
        if not free_text:
            return ()
        normalized = normalize_text(free_text)
        tags = IngredientTag.objects.filter(source="ania_gotuje")
        words = normalized.split()
        matches = []
        for tag in tags:
            tag_words = [word for word in normalize_text(tag.name).split() if len(word) >= 4]
            if tag_words and all(any(source_word.startswith(tag_word[:4]) for source_word in words) for tag_word in tag_words):
                matches.append(tag.name)
        return tuple(sorted(set(matches), key=len)[:3])
