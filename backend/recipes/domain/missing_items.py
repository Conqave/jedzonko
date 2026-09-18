from decimal import Decimal

from catalog.domain.measurement import Quantity
from inventory.domain.models import InventoryItemSnapshot
from recipes.domain.models import RecipeRequirement
from recipes.domain.suggestion import MissingRecipeItem


def scale_requirements(
    requirements: list[RecipeRequirement], recipe_servings: int, requested_servings: int
) -> list[RecipeRequirement]:
    factor = Decimal(requested_servings) / Decimal(recipe_servings)
    return [
        RecipeRequirement(
            ingredient_id=requirement.ingredient_id,
            ingredient_name=requirement.ingredient_name,
            quantity=Quantity(
                amount=requirement.quantity.amount * factor, unit=requirement.quantity.unit
            ),
        )
        for requirement in requirements
    ]


def calculate_missing_items(
    requirements: list[RecipeRequirement], inventory: list[InventoryItemSnapshot]
) -> list[MissingRecipeItem]:
    available_by_ingredient = {item.ingredient_id: item for item in inventory}
    missing: list[MissingRecipeItem] = []
    for requirement in requirements:
        required = requirement.quantity
        available = available_by_ingredient.get(requirement.ingredient_id)
        if available is None or not required.is_compatible_with(available.as_quantity()):
            missing.append(_to_missing_item(requirement, required.amount))
            continue
        remainder = required.subtract(available.as_quantity())
        if remainder.amount > 0:
            missing.append(_to_missing_item(requirement, remainder.amount))
    return missing


def _to_missing_item(requirement: RecipeRequirement, amount: Decimal) -> MissingRecipeItem:
    return MissingRecipeItem(
        ingredient_id=requirement.ingredient_id,
        ingredient_name=requirement.ingredient_name,
        amount=amount,
        unit_code=requirement.quantity.unit.code,
    )
