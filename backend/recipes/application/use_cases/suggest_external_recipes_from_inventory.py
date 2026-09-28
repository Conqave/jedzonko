from dataclasses import dataclass

from households.application.access import HouseholdAccessPolicy
from recipes.application.ports.household_inventory_reader import HouseholdInventoryReader
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import ExternalRecipePage, MatchedExternalRecipePage
from recipes.domain.matching import match_external_recipes


@dataclass(frozen=True, slots=True)
class ExternalRecipeSuggestions:
    page: MatchedExternalRecipePage
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
        selected_names: list[str] = []
        for item in ordered:
            candidates = item.tag_names
            for name in candidates:
                if name not in selected_names:
                    selected_names.append(name)
                if len(selected_names) >= self._ingredient_limit:
                    break
            if len(selected_names) >= self._ingredient_limit:
                break
        selected = tuple(selected_names)
        if not selected:
            return ExternalRecipeSuggestions(
                page=MatchedExternalRecipePage(
                    matches=(), page=page, page_size=page_size, total_count=0, total_pages=0
                ),
                ingredient_names=(),
                inventory_item_count=0,
            )
        # Ania Gotuje treats comma-separated ``ing`` values as an intersection.
        # Query each pantry tag separately, then merge the result set locally so
        # one missing pantry item cannot hide recipes matching the other items.
        summaries = {}
        for tag_name in selected:
            found = self._source.search_recipes("", (tag_name,), (), 0, page_size)
            for summary in found.recipes:
                summaries[summary.reference] = summary
        merged = sorted(summaries.values(), key=lambda summary: (summary.name, summary.reference))
        start = page * page_size
        page_recipes = tuple(merged[start : start + page_size])
        found = ExternalRecipePage(
            recipes=page_recipes,
            page=page,
            page_size=page_size,
            total_count=len(merged),
            total_pages=(len(merged) + page_size - 1) // page_size,
        )
        matched = match_external_recipes(found, inventory)
        useful_matches = tuple(match for match in matched.matches if match.matched_product_names)
        matched = MatchedExternalRecipePage(
            matches=useful_matches,
            page=page,
            page_size=page_size,
            total_count=len(useful_matches),
            total_pages=(len(useful_matches) + page_size - 1) // page_size,
        )
        return ExternalRecipeSuggestions(
            page=matched,
            ingredient_names=selected,
            inventory_item_count=len(inventory),
        )
