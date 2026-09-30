from dataclasses import dataclass

from recipes.domain.models import RecipeRequirement, RecipeSummary
from recipes.domain.nutrition import RecipeNutrition


@dataclass(frozen=True, slots=True)
class RecipeListing:
    summary: RecipeSummary
    nutrition: RecipeNutrition
    ingredient_names: tuple[str, ...]


def list_ingredient_names(
    requirements: list[RecipeRequirement], tag_names: dict[int, str]
) -> tuple[str, ...]:
    names = {requirement.name for requirement in requirements}
    for requirement in requirements:
        if requirement.ingredient_id is not None:
            names.add(tag_names[requirement.ingredient_id])
    return tuple(sorted(names))
