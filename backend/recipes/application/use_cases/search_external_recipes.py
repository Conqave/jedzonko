from dataclasses import dataclass

from households.application.access import HouseholdAccessPolicy
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import MatchedExternalRecipePage
from recipes.domain.matching import match_external_recipes


@dataclass(frozen=True, slots=True)
class ExternalRecipeQuery:
    household_id: int
    text: str
    ingredient_names: tuple[str, ...]
    excluded_ingredient_names: tuple[str, ...]
    page: int
    page_size: int


class SearchExternalRecipes:
    def __init__(
        self,
        source: RecipeSource,
        inventory_reader: HouseholdInventoryReader,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._source = source
        self._inventory_reader = inventory_reader
        self._access = access

    def execute(self, user_id: int, query: ExternalRecipeQuery) -> MatchedExternalRecipePage:
        self._access.require_membership(user_id, query.household_id)
        inventory = self._inventory_reader.read_inventory(user_id, query.household_id)
        page = self._source.search_recipes(
            query.text,
            query.ingredient_names,
            query.excluded_ingredient_names,
            query.page,
            query.page_size,
        )
        return match_external_recipes(page, inventory)
