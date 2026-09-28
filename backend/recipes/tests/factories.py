from decimal import Decimal

from recipes.domain.models import RecipeRequirement
from recipes.domain.stock import StockedProduct
from recipes.domain.suggestion import MissingRecipeItem
from shared.measurement import MeasurementDimension, MeasurementUnit, Quantity

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

FLOUR = 1
SUGAR = 2
EGGS = 3
MILK = 4


def make_requirement(
    name: str, amount: str, unit: MeasurementUnit, ingredient_id: int | None
) -> RecipeRequirement:
    quantity = Quantity(amount=Decimal(amount), unit=unit)
    return RecipeRequirement(name=name, ingredient_id=ingredient_id, quantity=quantity)


def make_stock(
    product_id: int,
    name: str,
    amount: str,
    unit: MeasurementUnit,
    ingredient_id: int | None,
    package: Quantity | None = None,
) -> StockedProduct:
    quantity = Quantity(amount=Decimal(amount), unit=unit)
    return StockedProduct(
        product_id=product_id,
        product_name=name,
        ingredient_id=ingredient_id,
        ingredient_name=None if ingredient_id is None else name.casefold(),
        quantity=quantity,
        package_content=package,
    )


def make_missing_item(name: str) -> MissingRecipeItem:
    return MissingRecipeItem(
        name=name, ingredient_id=None, stocked_product_id=None, amount=Decimal("1"), unit_code="g"
    )
