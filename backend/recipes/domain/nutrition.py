from dataclasses import dataclass
from decimal import Decimal

from recipes.domain.models import RecipeRequirement
from shared.nutrition import UncountedReason, count_kcal


@dataclass(frozen=True, slots=True)
class UncountedIngredient:
    name: str
    reason: UncountedReason


@dataclass(frozen=True, slots=True)
class RecipeNutrition:
    total_kcal: Decimal
    kcal_per_serving: Decimal | None
    uncounted_ingredients: tuple[UncountedIngredient, ...]


def list_tagged_ingredient_ids(requirements: list[RecipeRequirement]) -> set[int]:
    return {
        requirement.ingredient_id
        for requirement in requirements
        if requirement.ingredient_id is not None
    }


def summarize_nutrition(
    requirements: list[RecipeRequirement],
    kcal_per_100g_by_ingredient: dict[int, Decimal],
    servings: int | None,
) -> RecipeNutrition:
    if servings is not None and servings < 1:
        raise AssertionError(f"A recipe with {servings} servings passed a boundary unvalidated.")
    total_kcal = Decimal(0)
    uncounted: list[UncountedIngredient] = []
    for requirement in requirements:
        kcal_per_100g = _find_kcal_per_100g(requirement, kcal_per_100g_by_ingredient)
        counted = count_kcal(requirement.quantity, kcal_per_100g)
        if isinstance(counted, UncountedReason):
            uncounted.append(UncountedIngredient(name=requirement.name, reason=counted))
            continue
        total_kcal += counted
    kcal_per_serving = None if servings is None else total_kcal / servings
    return RecipeNutrition(
        total_kcal=total_kcal,
        kcal_per_serving=kcal_per_serving,
        uncounted_ingredients=tuple(uncounted),
    )


def _find_kcal_per_100g(
    requirement: RecipeRequirement, kcal_per_100g_by_ingredient: dict[int, Decimal]
) -> Decimal | None:
    if requirement.ingredient_id is None:
        return None
    return kcal_per_100g_by_ingredient.get(requirement.ingredient_id)
