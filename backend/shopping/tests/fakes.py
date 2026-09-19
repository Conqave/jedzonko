from decimal import Decimal

from catalog.domain.measurement import MeasurementDimension, MeasurementUnit
from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdMember, HouseholdSummary
from shopping.application.errors import ShoppingListItemNotFoundError, ShoppingListNotFoundError
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.application.ports.inventory_writer import InventoryWriter
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.inventory_stock_level import InventoryStockLevel
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_list_summary import ShoppingListSummary

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


class FakeHouseholdRepository(HouseholdRepository):
    def __init__(self, memberships: set[tuple[int, int]]) -> None:
        self._memberships = memberships

    def find_households_for_user(self, user_id: int) -> list[HouseholdSummary]:
        raise NotImplementedError

    def find_household(self, household_id: int) -> HouseholdSummary | None:
        raise NotImplementedError

    def is_member(self, user_id: int, household_id: int) -> bool:
        return (user_id, household_id) in self._memberships

    def list_members(self, household_id: int) -> list[HouseholdMember]:
        raise NotImplementedError

    def create_household(self, name: str, owner_user_id: int) -> HouseholdSummary:
        raise NotImplementedError

    def add_member(self, household_id: int, username: str) -> HouseholdMember:
        raise NotImplementedError

    def remove_member(self, household_id: int, user_id: int) -> None:
        raise NotImplementedError

    def count_members(self, household_id: int) -> int:
        raise NotImplementedError


class FakeShoppingListRepository(ShoppingListRepository):
    def __init__(self) -> None:
        self.lists: dict[int, tuple[int, str, bool]] = {}
        self.items: dict[int, tuple[int, ShoppingItemSnapshot]] = {}
        self._next_list_id = 1
        self._next_item_id = 1

    def seed_list(self, household_id: int, name: str, is_primary: bool) -> int:
        list_id = self._next_list_id
        self._next_list_id += 1
        self.lists[list_id] = (household_id, name, is_primary)
        return list_id

    def list_lists(self, household_id: int) -> list[ShoppingListSummary]:
        return [
            ShoppingListSummary(
                id=list_id,
                name=value[1],
                is_primary=value[2],
                item_count=len(self.list_items(list_id)),
            )
            for list_id, value in self.lists.items()
            if value[0] == household_id
        ]

    def get_or_create_primary_list(self, household_id: int) -> ShoppingListSummary:
        for list_id, value in self.lists.items():
            if value[0] == household_id and value[2]:
                return ShoppingListSummary(
                    id=list_id,
                    name=value[1],
                    is_primary=True,
                    item_count=len(self.list_items(list_id)),
                )
        list_id = self.seed_list(household_id, "Lista zakupów", True)
        return ShoppingListSummary(id=list_id, name="Lista zakupów", is_primary=True, item_count=0)

    def create_list(self, household_id: int, name: str) -> ShoppingListSummary:
        list_id = self.seed_list(household_id, name, False)
        return ShoppingListSummary(id=list_id, name=name, is_primary=False, item_count=0)

    def find_household_id_for_list(self, list_id: int) -> int | None:
        found = self.lists.get(list_id)
        return None if found is None else found[0]

    def find_household_id_for_item(self, item_id: int) -> int | None:
        found = self.items.get(item_id)
        if found is None or found[1].is_purchased:
            return None
        return self.find_household_id_for_list(found[0])

    def list_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        return [value[1] for value in self.items.values() if value[0] == list_id]

    def list_pending_items(self, list_id: int) -> list[ShoppingItemSnapshot]:
        return [item for item in self.list_items(list_id) if not item.is_purchased]

    def find_pending_item(self, item_id: int) -> ShoppingItemSnapshot | None:
        found = self.items.get(item_id)
        if found is None or found[1].is_purchased:
            return None
        return found[1]

    def find_pending_item_by_ingredient(
        self, list_id: int, ingredient_id: int
    ) -> ShoppingItemSnapshot | None:
        for item in self.list_pending_items(list_id):
            if item.ingredient_id == ingredient_id:
                return item
        return None

    def add_item(
        self,
        list_id: int,
        ingredient_id: int | None,
        free_text: str | None,
        quantity: Decimal,
        unit_code: str | None,
    ) -> ShoppingItemSnapshot:
        if list_id not in self.lists:
            raise ShoppingListNotFoundError
        item_id = self._next_item_id
        self._next_item_id += 1
        snapshot = ShoppingItemSnapshot(
            id=item_id,
            ingredient_id=ingredient_id,
            ingredient_name=None if ingredient_id is None else f"Składnik {ingredient_id}",
            free_text=free_text,
            quantity=quantity,
            unit=None if unit_code is None else UNITS[unit_code],
            is_purchased=False,
        )
        self.items[item_id] = (list_id, snapshot)
        return snapshot

    def set_item_quantity(
        self, item_id: int, quantity: Decimal, unit_code: str | None
    ) -> ShoppingItemSnapshot:
        found = self.items.get(item_id)
        if found is None:
            raise ShoppingListItemNotFoundError
        updated = ShoppingItemSnapshot(
            id=found[1].id,
            ingredient_id=found[1].ingredient_id,
            ingredient_name=found[1].ingredient_name,
            free_text=found[1].free_text,
            quantity=quantity,
            unit=None if unit_code is None else UNITS[unit_code],
            is_purchased=found[1].is_purchased,
        )
        self.items[item_id] = (found[0], updated)
        return updated

    def purchase_item(self, item_id: int) -> ShoppingItemSnapshot:
        found = self.items.get(item_id)
        if found is None or found[1].is_purchased:
            raise ShoppingListItemNotFoundError
        updated = ShoppingItemSnapshot(
            id=found[1].id,
            ingredient_id=found[1].ingredient_id,
            ingredient_name=found[1].ingredient_name,
            free_text=found[1].free_text,
            quantity=found[1].quantity,
            unit=found[1].unit,
            is_purchased=True,
        )
        self.items[item_id] = (found[0], updated)
        return updated

    def delete_item(self, item_id: int) -> None:
        if item_id not in self.items:
            raise ShoppingListItemNotFoundError
        del self.items[item_id]


class FakeHouseholdInventoryReader(HouseholdInventoryReader):
    def __init__(self, levels: list[InventoryStockLevel]) -> None:
        self.levels = levels

    def read_stock_levels(self, user_id: int, household_id: int) -> list[InventoryStockLevel]:
        return self.levels


class FakeInventoryWriter(InventoryWriter):
    def __init__(self) -> None:
        self.added: list[tuple[int, int, Decimal, str]] = []

    def add_purchased_quantity(
        self, household_id: int, ingredient_id: int, amount: Decimal, unit: MeasurementUnit
    ) -> None:
        self.added.append((household_id, ingredient_id, amount, unit.code))


class FakeRecipeRequirementReader(RecipeRequirementReader):
    def __init__(self, missing_items: list[MissingRecipeItem]) -> None:
        self.missing_items = missing_items

    def read_missing_items(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> list[MissingRecipeItem]:
        return self.missing_items
