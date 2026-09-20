from decimal import Decimal

from inventory.domain.models import InventoryItemSnapshot
from recipes.domain.matching import find_available_quantity, find_matching_item
from recipes.domain.models import RecipeRequirement
from recipes.domain.suggestion import MissingRecipeItem, RecipeShortfall
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


def calculate_shortfall(
    requirements: list[RecipeRequirement], inventory: list[InventoryItemSnapshot]
) -> RecipeShortfall:
    missing: list[MissingRecipeItem] = []
    unmeasured: list[str] = []
    for requirement in requirements:
        required = requirement.quantity
        item = find_matching_item(requirement.normalized_name, inventory)
        if item is None:
            missing.append(_to_missing_item(requirement, required.amount))
            continue
        available = find_available_quantity(item, required.unit)
        if available is None:
            unmeasured.append(requirement.name)
            missing.append(_to_missing_item(requirement, required.amount))
            continue
        remainder = required.subtract(available)
        if remainder.amount > 0:
            missing.append(_to_missing_item(requirement, remainder.amount))
    return RecipeShortfall(
        missing_items=tuple(missing),
        unmeasured_ingredient_names=tuple(unmeasured),
        required_item_count=len(requirements),
        available_item_count=len(requirements) - len(missing),
    )


def _to_missing_item(requirement: RecipeRequirement, amount: Decimal) -> MissingRecipeItem:
    return MissingRecipeItem(
        name=requirement.name,
        normalized_name=requirement.normalized_name,
        amount=amount,
        unit_code=requirement.quantity.unit.code,
    )
