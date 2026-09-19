from dataclasses import dataclass

from households.application.access import HouseholdAccessPolicy
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipePage


@dataclass(frozen=True, slots=True)
class ExternalRecipeSuggestions:
    page: ExternalRecipePage
    ingredient_names: tuple[str, ...]
    inventory_item_count: int


class SuggestExternalRecipesFromInventory:
    def __init__(
        self,
        source: RecipeSource,
        inventory_reader: HouseholdInventoryReader,
        access: HouseholdAccessPolicy,
        ingredient_limit: int,
    ) -> None:
        if ingredient_limit < 1:
            raise ValueError("ingredient_limit must be at least 1")
        self._source = source
        self._inventory_reader = inventory_reader
        self._access = access
        self._ingredient_limit = ingredient_limit

    def execute(
        self, user_id: int, household_id: int, page: int, page_size: int
    ) -> ExternalRecipeSuggestions:
        self._access.require_membership(user_id, household_id)
        inventory = self._inventory_reader.read_inventory(user_id, household_id)
        ordered = sorted(inventory, key=lambda item: item.normalized_name)
        selected = tuple(item.product_name for item in ordered[: self._ingredient_limit])
        if not selected:
            return ExternalRecipeSuggestions(
                page=ExternalRecipePage(
                    recipes=(), page=page, page_size=page_size, total_count=0, total_pages=0
                ),
                ingredient_names=(),
                inventory_item_count=0,
            )
        return ExternalRecipeSuggestions(
            page=self._source.search_recipes("", selected, (), page, page_size),
            ingredient_names=selected,
            inventory_item_count=len(inventory),
        )
