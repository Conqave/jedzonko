from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipeIngredient
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
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._source = source
        self._stock = stock
        self._resolver = resolver
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int, reference: str) -> RecipeShortfall:
        require_membership(self._memberships, user_id, household_id)
        recipe = self._source.get_recipe(reference)
        names = tuple(line.name for line in recipe.ingredients)
        ingredient_ids = self._resolver.find_ingredient_ids(names)
        requirements = [
            _to_requirement(line, ingredient_ids.get(line.name)) for line in recipe.ingredients
        ]
        stock = self._stock.get_stock(user_id, household_id)
        return calculate_shortfall(requirements, stock)


def _to_requirement(line: ExternalRecipeIngredient, ingredient_id: int | None) -> RecipeRequirement:
    quantity = None
    if line.quantity is not None and line.unit_code is not None:
        unit = find_measurement_unit(line.unit_code)
        if unit is None:
            raise AssertionError(f"The provider adapter let unit {line.unit_code!r} through.")
        quantity = Quantity(amount=line.quantity, unit=unit)
    return RecipeRequirement(name=line.name, ingredient_id=ingredient_id, quantity=quantity)
