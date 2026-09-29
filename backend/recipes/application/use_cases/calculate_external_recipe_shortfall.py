from decimal import Decimal

from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_lines import IngredientLines
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeIngredient
from recipes.domain.external_line import LineInterpretation
from recipes.domain.missing_items import calculate_shortfall
from recipes.domain.models import RecipeRequirement
from recipes.domain.suggestion import RecipeShortfall
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.measurement import Quantity
from shared.measurement_units import find_measurement_unit


class CalculateExternalRecipeShortfall:
    def __init__(
        self,
        source: RecipeSource,
        stock: HouseholdStockReader,
        resolver: IngredientResolver,
        lines: IngredientLines,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._source = source
        self._stock = stock
        self._resolver = resolver
        self._lines = lines
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int, reference: str) -> RecipeShortfall:
        require_membership(self._memberships, user_id, household_id)
        recipe = self._source.get_recipe(reference)
        names = tuple(line.name for line in recipe.ingredients)
        ingredient_ids = self._resolver.find_ingredient_ids(names)
        texts = tuple(line.source_text for line in recipe.ingredients)
        interpretations = self._lines.find_interpretations(texts)
        requirements = [
            _to_requirement(line, ingredient_ids.get(line.name), interpretations.get(text))
            for line, text in zip(recipe.ingredients, texts, strict=True)
        ]
        stock = self._stock.get_stock(user_id, household_id)
        return calculate_shortfall(requirements, stock)


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
