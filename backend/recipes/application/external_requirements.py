from decimal import Decimal

from recipes.application.external_content import read_external_content
from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeIngredient
from recipes.domain.external_line import LineInterpretation
from recipes.domain.models import RecipeRequirement
from shared.measurement import Quantity
from shared.measurement_units import find_measurement_unit


def read_external_requirements(
    catalog: ExternalRecipeCatalog,
    source: RecipeSource,
    resolver: IngredientResolver,
    lines: IngredientLines,
    reference: str,
) -> list[RecipeRequirement]:
    content = read_external_content(catalog, source, reference)
    return resolve_external_requirements(content.ingredients, resolver, lines)


def resolve_external_requirements(
    ingredients: tuple[ExternalRecipeIngredient, ...],
    resolver: IngredientResolver,
    lines: IngredientLines,
) -> list[RecipeRequirement]:
    names = tuple(line.name for line in ingredients)
    ingredient_ids = resolver.find_ingredient_ids(names)
    texts = tuple(line.source_text for line in ingredients)
    interpretations = lines.find_interpretations(texts)
    return [
        _to_requirement(line, ingredient_ids.get(line.name), interpretations.get(text))
        for line, text in zip(ingredients, texts, strict=True)
    ]


def _to_requirement(
    line: ExternalRecipeIngredient,
    exact_ingredient_id: int | None,
    interpretation: LineInterpretation | None,
) -> RecipeRequirement:
    if interpretation is None:
        amount = _to_quantity(line.quantity, line.unit_code)
        return RecipeRequirement(name=line.name, ingredient_id=exact_ingredient_id, quantity=amount)
    ingredient_id = (
        interpretation.ingredient_id if exact_ingredient_id is None else exact_ingredient_id
    )
    parsed = _to_quantity(line.quantity, line.unit_code)
    interpreted = _to_quantity(interpretation.quantity, interpretation.unit_code)
    quantity = interpreted if parsed is None else parsed
    return RecipeRequirement(name=line.name, ingredient_id=ingredient_id, quantity=quantity)


def _to_quantity(amount: Decimal | None, unit_code: str | None) -> Quantity | None:
    if amount is None or unit_code is None:
        return None
    unit = find_measurement_unit(unit_code)
    if unit is None:
        raise AssertionError(f"Unit {unit_code!r} passed a boundary unvalidated.")
    return Quantity(amount=amount, unit=unit)
