from dataclasses import dataclass

from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import (
    ExternalRecipePage,
    MatchedExternalRecipePage,
    with_local_images,
)
from recipes.domain.matching import match_external_recipes
from shared.household_membership import HouseholdMembershipReader, require_membership


@dataclass(frozen=True, slots=True)
class ExternalRecipeSuggestions:
    page: MatchedExternalRecipePage
    ingredient_names: tuple[str, ...]
    inventory_item_count: int


class SuggestExternalRecipesFromInventory:
    def __init__(
        self,
        catalog: ExternalRecipeCatalog,
        source: RecipeSource,
        stock: HouseholdStockReader,
        resolver: IngredientResolver,
        memberships: HouseholdMembershipReader,
        ingredient_limit: int,
    ) -> None:
        if ingredient_limit < 1:
            raise ValueError("ingredient_limit must be at least 1")
        self._catalog = catalog
        self._source = source
        self._stock = stock
        self._resolver = resolver
        self._memberships = memberships
        self._ingredient_limit = ingredient_limit

    def execute(
        self, user_id: int, household_id: int, page: int, page_size: int
    ) -> ExternalRecipeSuggestions:
        require_membership(self._memberships, user_id, household_id)
        inventory = self._stock.get_stock(user_id, household_id)
        selected_names: list[str] = []
        for product in sorted(inventory, key=lambda product: product.product_name):
            for name in product.tag_names:
                if name not in selected_names:
                    selected_names.append(name)
        selected = tuple(selected_names[: self._ingredient_limit])
        if not selected:
            return ExternalRecipeSuggestions(
                page=MatchedExternalRecipePage(
                    matches=(), page=page, page_size=page_size, total_count=0, total_pages=0
                ),
                ingredient_names=(),
                inventory_item_count=0,
            )
        summaries = {}
        for ingredient_name in selected:
            found = self._source.search_recipes("", (ingredient_name,), (), 0, page_size)
            for summary in found.recipes:
                summaries[summary.reference] = summary
        merged = sorted(summaries.values(), key=lambda summary: (summary.name, summary.reference))
        start = page * page_size
        page_recipes = tuple(merged[start : start + page_size])
        paged = ExternalRecipePage(
            recipes=page_recipes,
            page=page,
            page_size=page_size,
            total_count=len(merged),
            total_pages=(len(merged) + page_size - 1) // page_size,
        )
        references = tuple(summary.reference for summary in page_recipes)
        local_image_urls = self._catalog.find_image_urls(references)
        found = with_local_images(paged, local_image_urls)
        tag_names = tuple({name for summary in found.recipes for name in summary.tag_names})
        ingredient_ids = self._resolver.find_ingredient_ids(tag_names)
        matched = match_external_recipes(found, inventory, ingredient_ids)
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
