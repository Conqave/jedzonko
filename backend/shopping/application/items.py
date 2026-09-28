from decimal import Decimal

from shared.measurement_units import find_measurement_unit
from shopping.application.errors import (
    IngredientNotFoundError,
    InvalidShoppingItemError,
    ProductNotFoundError,
)
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot
from shopping.domain.shopping_subject import ShoppingSubject


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
