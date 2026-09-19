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


def make_requirement(name: str, amount: str, unit: MeasurementUnit) -> RecipeRequirement:
    return RecipeRequirement(
        name=name,
        normalized_name=normalize_text(name),
        quantity=Quantity(amount=Decimal(amount), unit=unit),
    )


def make_snapshot(
    product_id: int, name: str, amount: str, unit: MeasurementUnit
) -> InventoryItemSnapshot:
    return InventoryItemSnapshot(
        id=product_id,
        product_id=product_id,
        product_name=name,
        normalized_name=normalize_text(name),
        quantity=Decimal(amount),
        unit=unit,
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
