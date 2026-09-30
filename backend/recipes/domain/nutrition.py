from dataclasses import dataclass
from decimal import Decimal

from recipes.domain.models import RecipeRequirement
from shared.nutrition import NutritionFacts, UncountedReason, count_kcal


@dataclass(frozen=True, slots=True)
class UncountedIngredient:
    name: str
    reason: UncountedReason


@dataclass(frozen=True, slots=True)
class RecipeNutrition:
    total_kcal: Decimal
    kcal_per_serving: Decimal | None
    has_estimates: bool
    uncounted_ingredients: tuple[UncountedIngredient, ...]


def list_tagged_ingredient_ids(requirements: list[RecipeRequirement]) -> set[int]:
    return {
        requirement.ingredient_id
        for requirement in requirements
        if requirement.ingredient_id is not None
    }


def summarize_nutrition(
    requirements: list[RecipeRequirement],
    facts_by_ingredient: dict[int, NutritionFacts],
    servings: int | None,
) -> RecipeNutrition:
    if servings is not None and servings < 1:
        raise AssertionError(f"A recipe with {servings} servings passed a boundary unvalidated.")
    total_kcal = Decimal(0)
    has_estimates = False
    uncounted: list[UncountedIngredient] = []
    for requirement in requirements:
        facts = _find_facts(requirement, facts_by_ingredient)
        counted = count_kcal(requirement.quantity, facts)
        if isinstance(counted, UncountedReason):
            uncounted.append(UncountedIngredient(name=requirement.name, reason=counted))
            continue
        total_kcal += counted.kcal
        has_estimates = has_estimates or counted.is_estimate
    kcal_per_serving = None if servings is None else total_kcal / servings
    return RecipeNutrition(
        total_kcal=total_kcal,
        kcal_per_serving=kcal_per_serving,
        has_estimates=has_estimates,
        uncounted_ingredients=tuple(uncounted),
    )


def _find_facts(
    requirement: RecipeRequirement, facts_by_ingredient: dict[int, NutritionFacts]
) -> NutritionFacts | None:
    if requirement.ingredient_id is None:
        return None
    return facts_by_ingredient.get(requirement.ingredient_id)
