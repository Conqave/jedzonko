from decimal import Decimal

from shared.measurement_units import find_measurement_unit
from shopping.application.errors import (
    IngredientNotFoundError,
    InvalidShoppingItemError,
    ProductNotFoundError,
)
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_subject import ShoppingSubject

UNQUANTIFIED_AMOUNT = Decimal("1")


def require_known_subject(
    catalog: CatalogDirectory, household_id: int, subject: ShoppingSubject
) -> None:
    if subject.product_id is not None and not catalog.is_household_product(
        household_id, subject.product_id
    ):
        raise ProductNotFoundError
    if subject.ingredient_id is not None and not catalog.has_ingredient(subject.ingredient_id):
        raise IngredientNotFoundError


def require_valid_amount(
    subject: ShoppingSubject, quantity: Decimal, unit_code: str | None
) -> None:
    if quantity <= 0:
        raise InvalidShoppingItemError
    if unit_code is None and subject.is_measured:
        raise InvalidShoppingItemError
    if unit_code is not None and find_measurement_unit(unit_code) is None:
        raise InvalidShoppingItemError


def add_to_list(
    repository: ShoppingListRepository,
    list_id: int,
    subject: ShoppingSubject,
    quantity: Decimal,
    unit_code: str | None,
) -> ShoppingItemSnapshot:
    existing = repository.find_pending_item(list_id, subject)
    if existing is None:
        return repository.add_item(list_id, subject, quantity, unit_code)
    if _unit_code(existing) != unit_code:
        raise InvalidShoppingItemError
    return repository.set_item_quantity(existing.id, existing.quantity + quantity, unit_code)


def ensure_on_list(
    repository: ShoppingListRepository,
    list_id: int,
    subject: ShoppingSubject,
    quantity: Decimal,
    unit_code: str,
) -> None:
    existing = repository.find_pending_item(list_id, subject)
    if existing is None:
        repository.add_item(list_id, subject, quantity, unit_code)
        return
    if _unit_code(existing) == unit_code and existing.quantity >= quantity:
        return
    repository.set_item_quantity(existing.id, quantity, unit_code)


def _unit_code(item: ShoppingItemSnapshot) -> str | None:
    return None if item.unit is None else item.unit.code


def put_missing_items_on_list(
    repository: ShoppingListRepository,
    catalog: CatalogDirectory,
    household_id: int,
    list_id: int,
    missing: list[MissingRecipeItem],
) -> None:
    for item in missing:
        known_product = _find_only_product(catalog, household_id, item)
        subject = item.subject(known_product)
        if item.amount is None or item.unit_code is None:
            text_subject = ShoppingSubject(free_text=item.name)
            if repository.find_pending_item(list_id, text_subject) is None:
                repository.add_item(list_id, text_subject, UNQUANTIFIED_AMOUNT, None)
            continue
        ensure_on_list(repository, list_id, subject, item.amount, item.unit_code)


def _find_only_product(
    catalog: CatalogDirectory, household_id: int, item: MissingRecipeItem
) -> int | None:
    if item.stocked_product_id is not None or item.ingredient_id is None:
        return None
    return catalog.find_only_product_of_ingredient(household_id, item.ingredient_id)
