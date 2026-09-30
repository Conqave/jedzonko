from dataclasses import dataclass

from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import MatchedExternalRecipePage, with_local_images
from recipes.domain.matching import match_external_recipes
from shared.household_membership import HouseholdMembershipReader, require_membership


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
        catalog: ExternalRecipeCatalog,
        source: RecipeSource,
        stock: HouseholdStockReader,
        resolver: IngredientResolver,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._catalog = catalog
        self._source = source
        self._stock = stock
        self._resolver = resolver
        self._memberships = memberships

    def execute(self, user_id: int, query: ExternalRecipeQuery) -> MatchedExternalRecipePage:
        require_membership(self._memberships, user_id, query.household_id)
        stock = self._stock.get_stock(user_id, query.household_id)
        found = self._source.search_recipes(
            query.text,
            query.ingredient_names,
            query.excluded_ingredient_names,
            query.page,
            query.page_size,
        )
        references = tuple(summary.reference for summary in found.recipes)
        local_image_urls = self._catalog.find_image_urls(references)
        page = with_local_images(found, local_image_urls)
        tag_names = tuple({name for summary in page.recipes for name in summary.tag_names})
        ingredient_ids = self._resolver.find_ingredient_ids(tag_names)
        return match_external_recipes(page, stock, ingredient_ids)
