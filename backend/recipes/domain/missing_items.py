from decimal import Decimal

from recipes.domain.matching import find_stock
from recipes.domain.models import RecipeRequirement
from recipes.domain.stock import StockedProduct
from recipes.domain.suggestion import MissingRecipeItem, RecipeShortfall
from shared.measurement import Quantity


def scale_requirements(
    requirements: list[RecipeRequirement], recipe_servings: int, requested_servings: int
) -> list[RecipeRequirement]:
    factor = Decimal(requested_servings) / Decimal(recipe_servings)
    return [
        RecipeRequirement(
            name=requirement.name,
            ingredient_id=requirement.ingredient_id,
            quantity=Quantity(
                amount=requirement.quantity.amount * factor, unit=requirement.quantity.unit
            ),
        )
        for requirement in requirements
    ]


def calculate_shortfall(
    requirements: list[RecipeRequirement], stock: list[StockedProduct]
) -> RecipeShortfall:
    missing: list[MissingRecipeItem] = []
    unmeasured: list[str] = []
    for requirement in requirements:
        required = requirement.quantity
        match = find_stock(requirement.ingredient_id, required.unit, stock)
        if match is None:
            absent = _to_missing_item(requirement, None, required.amount)
            missing.append(absent)
            continue
        if match.available is None:
            unmeasured.append(requirement.name)
            incomparable = _to_missing_item(requirement, match.product.product_id, required.amount)
            missing.append(incomparable)
            continue
        remainder = required.subtract(match.available)
        if remainder.amount > 0:
            short = _to_missing_item(requirement, match.product.product_id, remainder.amount)
            missing.append(short)
    return RecipeShortfall(
        missing_items=tuple(missing),
        unmeasured_ingredient_names=tuple(unmeasured),
        required_item_count=len(requirements),
        available_item_count=len(requirements) - len(missing),
    )


def _to_missing_item(
    requirement: RecipeRequirement, stocked_product_id: int | None, amount: Decimal
) -> MissingRecipeItem:
    return MissingRecipeItem(
        name=requirement.name,
        ingredient_id=requirement.ingredient_id,
        stocked_product_id=stocked_product_id,
        amount=amount,
        unit_code=requirement.quantity.unit.code,
    )
