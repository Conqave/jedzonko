from decimal import Decimal

from inventory.domain.models import InventoryItemSnapshot
from recipes.domain.models import RecipeRequirement
from recipes.domain.suggestion import MissingRecipeItem
from shared.measurement import MeasurementDimension, MeasurementUnit, Quantity
from shared.text import normalize_text

GRAM = MeasurementUnit(code="g", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1"))
KILOGRAM = MeasurementUnit(
    code="kg", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1000")
)
MILLILITRE = MeasurementUnit(
    code="ml", dimension=MeasurementDimension.VOLUME, factor_to_base=Decimal("1")
)
PIECE = MeasurementUnit(
    code="szt", dimension=MeasurementDimension.COUNT, factor_to_base=Decimal("1")
)
PACKAGE = MeasurementUnit(
    code="opak", dimension=MeasurementDimension.COUNT, factor_to_base=Decimal("1")
)


def make_requirement(name: str, amount: str, unit: MeasurementUnit) -> RecipeRequirement:
    return RecipeRequirement(
        name=name,
        normalized_name=normalize_text(name),
        quantity=Quantity(amount=Decimal(amount), unit=unit),
    )


def make_snapshot(
    product_id: int,
    name: str,
    amount: str,
    unit: MeasurementUnit,
    alias_names: tuple[str, ...] = (),
    package_quantity: str | None = None,
    package_unit: MeasurementUnit | None = None,
) -> InventoryItemSnapshot:
    return InventoryItemSnapshot(
        id=product_id,
        product_id=product_id,
        product_name=name,
        normalized_name=normalize_text(name),
        alias_names=tuple(normalize_text(alias) for alias in alias_names),
        quantity=Decimal(amount),
        unit=unit,
        package_quantity=None if package_quantity is None else Decimal(package_quantity),
        package_unit=package_unit,
        minimum_quantity=None,
        category_id=None,
        category_name=None,
        photo_url=None,
    )


def make_missing_item(name: str) -> MissingRecipeItem:
    return MissingRecipeItem(
        name=name,
        normalized_name=normalize_text(name),
        amount=Decimal("1"),
        unit_code="g",
    )
