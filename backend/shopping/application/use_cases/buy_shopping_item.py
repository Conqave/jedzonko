from datetime import datetime

from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.measurement import MeasurementUnit
from shared.measurement_units import BASE_UNIT_CODES
from shared.transactions import TransactionManager
from shopping.application.errors import (
    ChosenProductNotTaggedError,
    IngredientNotFoundError,
    InvalidShoppingItemError,
    ShoppingItemProductAmbiguousError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.inventory_writer import InventoryWriter
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.application.ports.tagged_product_creator import TaggedProductCreator
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_purchase import ShoppingPurchase


class BuyShoppingItem:

    def __init__(
        self,
        repository: ShoppingListRepository,
        inventory: InventoryWriter,
        catalog: CatalogDirectory,
        products: TaggedProductCreator,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._inventory = inventory
        self._catalog = catalog
        self._products = products
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, purchase: ShoppingPurchase, now: datetime) -> None:
        item = self._repository.find_item(purchase.item_id)
        if item is None or item.is_purchased:
            raise ShoppingListItemNotFoundError
        shopping_list = self._repository.find_list(item.list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        with self._transactions.atomic():
            product_id = self._find_product(
                user_id, shopping_list.household_id, item, purchase, now
            )
            self._repository.mark_purchased(item.id, now)
            if product_id is not None:
                unit = _require_unit(item)
                self._inventory.add_purchased_quantity(
                    shopping_list.household_id, product_id, item.quantity, unit
                )

    def _find_product(
        self,
        user_id: int,
        household_id: int,
        item: ShoppingItemSnapshot,
        purchase: ShoppingPurchase,
        now: datetime,
    ) -> int | None:
        ingredient_id = item.subject.ingredient_id
        if ingredient_id is not None:
            return self._find_tagged_product(
                user_id, household_id, item, ingredient_id, purchase, now
            )
        if purchase.chosen_product_id is not None:
            raise InvalidShoppingItemError
        return item.subject.product_id

    def _find_tagged_product(
        self,
        user_id: int,
        household_id: int,
        item: ShoppingItemSnapshot,
        ingredient_id: int,
        purchase: ShoppingPurchase,
        now: datetime,
    ) -> int:
        product_ids = self._catalog.list_products_of_ingredient(household_id, ingredient_id)
        if purchase.chosen_product_id is not None:
            if purchase.chosen_product_id not in product_ids:
                raise ChosenProductNotTaggedError
            return purchase.chosen_product_id
        if len(product_ids) > 1:
            raise ShoppingItemProductAmbiguousError
        if len(product_ids) == 1:
            return product_ids[0]
        return self._create_tag_product(user_id, household_id, item, ingredient_id, now)

    def _create_tag_product(
        self,
        user_id: int,
        household_id: int,
        item: ShoppingItemSnapshot,
        ingredient_id: int,
        now: datetime,
    ) -> int:
        name = self._catalog.find_ingredient_name(ingredient_id)
        if name is None:
            raise IngredientNotFoundError
        unit = _require_unit(item)
        unit_code = BASE_UNIT_CODES[unit.dimension]
        return self._products.create_tagged_product(
            user_id, household_id, ingredient_id, name, unit_code, now
        )


def _require_unit(item: ShoppingItemSnapshot) -> MeasurementUnit:
    if item.unit is None:
        raise AssertionError("A measured shopping item has no unit.")
    return item.unit
