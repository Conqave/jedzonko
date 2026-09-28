from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import replace
from datetime import datetime
from decimal import Decimal

from shared.household_membership import HouseholdMembershipReader
from shared.measurement import MeasurementDimension, MeasurementUnit
from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListItemNotFoundError, ShoppingListNotFoundError
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.application.ports.inventory_writer import InventoryWriter
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.inventory_stock_level import InventoryStockLevel
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_item_status import ShoppingItemStatus
from shopping.domain.shopping_list_summary import ShoppingListSummary
from shopping.domain.shopping_subject import ShoppingSubject

UNITS = {
    "g": MeasurementUnit(
        code="g", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1")
    ),
    "kg": MeasurementUnit(
        code="kg", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1000")
    ),
    "szt": MeasurementUnit(
        code="szt", dimension=MeasurementDimension.COUNT, factor_to_base=Decimal("1")
    ),
}


class FakeHouseholdMembershipReader(HouseholdMembershipReader):
    def __init__(self, memberships: set[tuple[int, int]]) -> None:
        self._memberships = memberships

    def is_member(self, user_id: int, household_id: int) -> bool:
        return (user_id, household_id) in self._memberships


class FakeTransactionManager(TransactionManager):
    def __init__(self) -> None:
        self.opened = 0

    def atomic(self) -> AbstractContextManager[None]:
        return self._atomic()

    @contextmanager
    def _atomic(self) -> Iterator[None]:
        self.opened += 1
        yield


class FakeShoppingListRepository(ShoppingListRepository):

    def __init__(self) -> None:
        self.lists: dict[int, ShoppingListSummary] = {}
        self.items: dict[int, ShoppingItemSnapshot] = {}
        self._next_list_id = 1
        self._next_item_id = 1

    def list_lists(self, household_id: int) -> list[ShoppingListSummary]:
        return [
            self._summary(each.id)
            for each in self.lists.values()
            if each.household_id == household_id
        ]

    def find_list(self, list_id: int) -> ShoppingListSummary | None:
        return None if list_id not in self.lists else self._summary(list_id)

    def find_primary_list(self, household_id: int) -> ShoppingListSummary | None:
        for each in self.lists.values():
            if each.household_id == household_id and each.is_primary:
                return self._summary(each.id)
        return None

    def create_list(self, household_id: int, name: str, is_primary: bool) -> ShoppingListSummary:
        if is_primary and self.find_primary_list(household_id) is not None:
            raise AssertionError("Unique constraint on the primary list violated.")
        summary = ShoppingListSummary(
            id=self._next_list_id,
            household_id=household_id,
            name=name,
            is_primary=is_primary,
            item_count=0,
        )
        self._next_list_id += 1
        self.lists[summary.id] = summary
        return summary

    def rename_list(self, list_id: int, name: str) -> ShoppingListSummary:
        self.lists[list_id] = replace(self.lists[list_id], name=name)
        return self._summary(list_id)

    def delete_list(self, list_id: int) -> None:
        del self.lists[list_id]
        self.items = {key: item for key, item in self.items.items() if item.list_id != list_id}

    def find_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        return self.items.get(item_id)

    def list_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        return [item for item in self.items.values() if item.list_id == list_id]

    def list_pending_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        return [item for item in self.list_items(list_id) if not item.is_purchased]

    def find_pending_item(
        self, list_id: int, subject: ShoppingSubject
    ) -> ShoppingItemSnapshot | None:
        for item in self.list_pending_items(list_id):
            if item.subject == subject:
                return item
        return None

    def add_item(
        self, list_id: int, subject: ShoppingSubject, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        if list_id not in self.lists:
            raise ShoppingListNotFoundError
        if subject.free_text is None and self.find_pending_item(list_id, subject) is not None:
            raise AssertionError("Unique constraint on the pending subject violated.")
        item = ShoppingItemSnapshot(
            id=self._next_item_id,
            list_id=list_id,
            subject=subject,
            name=subject.free_text or f"subject {subject.product_id or subject.ingredient_id}",
            quantity=quantity,
            unit=None if unit_code is None else UNITS[unit_code],
            status=ShoppingItemStatus.PENDING,
            purchased_at=None,
        )
        self._next_item_id += 1
        self.items[item.id] = item
        return item

    def set_item_quantity(
        self, item_id: int, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        unit = None if unit_code is None else UNITS[unit_code]
        self.items[item_id] = replace(self._item(item_id), quantity=quantity, unit=unit)
        return self.items[item_id]

    def mark_purchased(self, item_id: int, purchased_at: datetime) -> ShoppingItemSnapshot:
        item = self._item(item_id)
        if item.is_purchased:
            raise ShoppingListItemNotFoundError
        self.items[item_id] = replace(
            item, status=ShoppingItemStatus.PURCHASED, purchased_at=purchased_at
        )
        return self.items[item_id]

    def mark_pending(self, item_id: int) -> ShoppingItemSnapshot:
        item = self._item(item_id)
        self.items[item_id] = replace(item, status=ShoppingItemStatus.PENDING, purchased_at=None)
        return self.items[item_id]

    def delete_item(self, item_id: int) -> None:
        self._item(item_id)
        del self.items[item_id]

    def list_items_about_ingredient(self, ingredient_id: int) -> list[ShoppingItemSnapshot]:
        return [item for item in self.items.values() if item.subject.ingredient_id == ingredient_id]

    def set_item_ingredient(self, item_id: int, ingredient_id: int) -> None:
        item = self._item(item_id)
        self.items[item_id] = replace(item, subject=ShoppingSubject(ingredient_id=ingredient_id))

    def _item(self, item_id: int) -> ShoppingItemSnapshot:
        item = self.items.get(item_id)
        if item is None:
            raise ShoppingListItemNotFoundError
        return item

    def _summary(self, list_id: int) -> ShoppingListSummary:
        count = len(self.list_items(list_id))
        return replace(self.lists[list_id], item_count=count)


class FakeCatalogDirectory(CatalogDirectory):
    def __init__(
        self,
        products: dict[int, int],
        ingredient_ids: set[int],
        only_products: dict[int, int] | None = None,
    ) -> None:
        self._household_by_product = products
        self._ingredient_ids = ingredient_ids
        self._only_products = {} if only_products is None else only_products

    def is_household_product(self, household_id: int, product_id: int) -> bool:
        return self._household_by_product.get(product_id) == household_id

    def has_ingredient(self, ingredient_id: int) -> bool:
        return ingredient_id in self._ingredient_ids

    def find_only_product_of_ingredient(self, household_id: int, ingredient_id: int) -> int | None:
        return self._only_products.get(ingredient_id)


class FakeInventoryReader(HouseholdInventoryReader):
    def __init__(self, levels: list[InventoryStockLevel]) -> None:
        self._levels = levels

    def get_stock_levels(self, user_id: int, household_id: int) -> list[InventoryStockLevel]:
        return self._levels


class FakeInventoryWriter(InventoryWriter):
    def __init__(self) -> None:
        self.added: list[tuple[int, int, Decimal, str]] = []

    def add_purchased_quantity(
        self, household_id: int, product_id: int, amount: Decimal, unit: MeasurementUnit
    ) -> None:
        self.added.append((household_id, product_id, amount, unit.code))


class FakeRecipeRequirementReader(RecipeRequirementReader):
    def __init__(self, missing: list[MissingRecipeItem]) -> None:
        self._missing = missing

    def get_missing_items(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> list[MissingRecipeItem]:
        return self._missing

    def get_missing_external_items(
        self, user_id: int, household_id: int, reference: str
    ) -> list[MissingRecipeItem]:
        return self._missing
