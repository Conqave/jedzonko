from decimal import Decimal

from inventory.domain.models import InventoryItemSnapshot
from recipes.domain.models import RecipeRequirement
from recipes.domain.suggestion import MissingRecipeItem
from shared.measurement import Quantity


def scale_requirements(
    requirements: list[RecipeRequirement], recipe_servings: int, requested_servings: int
) -> list[RecipeRequirement]:
    factor = Decimal(requested_servings) / Decimal(recipe_servings)
    return [
        RecipeRequirement(
            name=requirement.name,
            normalized_name=requirement.normalized_name,
            quantity=Quantity(
                amount=requirement.quantity.amount * factor, unit=requirement.quantity.unit
            ),
        )
        for requirement in requirements
    ]


def calculate_missing_items(
    requirements: list[RecipeRequirement], inventory: list[InventoryItemSnapshot]
) -> list[MissingRecipeItem]:
    available_by_name = {item.normalized_name: item for item in inventory}
    missing: list[MissingRecipeItem] = []
    for requirement in requirements:
        required = requirement.quantity
        available = available_by_name.get(requirement.normalized_name)
        if available is None or not required.is_compatible_with(available.as_quantity()):
            missing.append(_to_missing_item(requirement, required.amount))
            continue
        remainder = required.subtract(available.as_quantity())
        if remainder.amount > 0:
            missing.append(_to_missing_item(requirement, remainder.amount))
    return missing


def _to_missing_item(requirement: RecipeRequirement, amount: Decimal) -> MissingRecipeItem:
    return MissingRecipeItem(
        name=requirement.name,
        normalized_name=requirement.normalized_name,
        amount=amount,
        unit_code=requirement.quantity.unit.code,
    )
