from decimal import Decimal

from catalog.domain.measurement import MeasurementDimension, MeasurementUnit, Quantity
from inventory.domain.models import InventoryItemSnapshot
from recipes.domain.models import RecipeRequirement

GRAM = MeasurementUnit(code="g", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1"))
KILOGRAM = MeasurementUnit(
    code="kg", dimension=MeasurementDimension.MASS, factor_to_base=Decimal("1000")
)
MILLILITRE = MeasurementUnit(
    code="ml", dimension=MeasurementDimension.VOLUME, factor_to_base=Decimal("1")
)


def make_requirement(
    ingredient_id: int, name: str, amount: str, unit: MeasurementUnit
) -> RecipeRequirement:
    return RecipeRequirement(
        ingredient_id=ingredient_id,
        ingredient_name=name,
        quantity=Quantity(amount=Decimal(amount), unit=unit),
    )


def make_snapshot(
    ingredient_id: int, name: str, amount: str, unit: MeasurementUnit
) -> InventoryItemSnapshot:
    return InventoryItemSnapshot(
        id=ingredient_id,
        ingredient_id=ingredient_id,
        ingredient_name=name,
        quantity=Decimal(amount),
        unit=unit,
        minimum_quantity=None,
        category_name=None,
        photo_url=None,
    )
