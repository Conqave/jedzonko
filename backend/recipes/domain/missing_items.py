from decimal import Decimal

from recipes.domain.matching import find_stock, has_stock
from recipes.domain.models import RecipeRequirement
from recipes.domain.stock import StockedProduct
from recipes.domain.suggestion import MissingRecipeItem, RecipeShortfall
from shared.measurement import Quantity


def scale_requirements(
    requirements: list[RecipeRequirement], recipe_servings: int, requested_servings: int
) -> list[RecipeRequirement]:
    factor = Decimal(requested_servings) / Decimal(recipe_servings)
    scaled: list[RecipeRequirement] = []
    for requirement in requirements:
        quantity = requirement.quantity
        if quantity is not None:
            quantity = Quantity(amount=quantity.amount * factor, unit=quantity.unit)
        scaled.append(
            RecipeRequirement(
                name=requirement.name, ingredient_id=requirement.ingredient_id, quantity=quantity
            )
        )
    return scaled


def calculate_shortfall(
    requirements: list[RecipeRequirement], stock: list[StockedProduct]
) -> RecipeShortfall:
    missing: list[MissingRecipeItem] = []
    unmeasured: list[str] = []
    for requirement in requirements:
        required = requirement.quantity
        if required is None:
            if not has_stock(requirement.ingredient_id, stock):
                unquantified = _to_missing_item(requirement, None, None)
                missing.append(unquantified)
            continue
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
    requirement: RecipeRequirement, stocked_product_id: int | None, amount: Decimal | None
) -> MissingRecipeItem:
    quantity = requirement.quantity
    unit_code = None if quantity is None else quantity.unit.code
    return MissingRecipeItem(
        name=requirement.name,
        ingredient_id=requirement.ingredient_id,
        stocked_product_id=stocked_product_id,
        amount=amount,
        unit_code=unit_code,
    )
