from recipes.application.commands import RecipeIngredientInput, ResolvedIngredient
from recipes.application.errors import DuplicateRecipeIngredientError, MeasurementUnitNotFoundError
from recipes.application.ports.ingredient_resolver import IngredientResolver
from shared.measurement_units import find_measurement_unit
from shared.text import normalize_text


def resolve_recipe_ingredients(
    lines: tuple[RecipeIngredientInput, ...], resolver: IngredientResolver
) -> tuple[ResolvedIngredient, ...]:
    seen: set[str] = set()
    for line in lines:
        if find_measurement_unit(line.unit_code) is None:
            raise MeasurementUnitNotFoundError
        normalized_name = normalize_text(line.name)
        if normalized_name in seen:
            raise DuplicateRecipeIngredientError
        seen.add(normalized_name)
    names = tuple(line.name for line in lines)
    ingredient_ids = resolver.find_ingredient_ids(names)
    resolved: list[ResolvedIngredient] = []
    for line in lines:
        normalized_name = normalize_text(line.name)
        resolved.append(
            ResolvedIngredient(
                name=line.name,
                normalized_name=normalized_name,
                ingredient_id=ingredient_ids.get(line.name),
                quantity=line.quantity,
                unit_code=line.unit_code,
            )
        )
    return tuple(resolved)
