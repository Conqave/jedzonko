from dataclasses import dataclass

from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.application.ports.ingredient_resolver import IngredientResolver
from recipes.application.ports.recipe_source import RecipeSource
from recipes.domain.external import MatchedExternalRecipePage
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
        source: RecipeSource,
        stock: HouseholdStockReader,
        resolver: IngredientResolver,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._source = source
        self._stock = stock
        self._resolver = resolver
        self._memberships = memberships

    def execute(self, user_id: int, query: ExternalRecipeQuery) -> MatchedExternalRecipePage:
        require_membership(self._memberships, user_id, query.household_id)
        stock = self._stock.get_stock(user_id, query.household_id)
        page = self._source.search_recipes(
            query.text,
            query.ingredient_names,
            query.excluded_ingredient_names,
            query.page,
            query.page_size,
        )
        tag_names = tuple({name for summary in page.recipes for name in summary.tag_names})
        ingredient_ids = self._resolver.find_ingredient_ids(tag_names)
        return match_external_recipes(page, stock, ingredient_ids)
