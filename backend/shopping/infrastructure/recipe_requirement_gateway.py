from collections.abc import Callable
from contextlib import AbstractContextManager

from recipes.application.errors import (
    RecipeNotFoundAtSourceError,
    RecipeSourceContractError,
    RecipeSourceUnavailableError,
)
from recipes.application.use_cases.calculate_missing_recipe_items import (
    CalculateMissingRecipeItems,
)
from recipes.application.use_cases.external_recipes import ExternalRecipes
from recipes.domain.suggestion import RecipeShortfall
from shopping.application.errors import ExternalRecipeNotFoundError, RecipesUnavailableError
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.domain.missing_recipe_item import MissingRecipeItem


class RecipeRequirementGateway(RecipeRequirementReader):
    def __init__(
        self,
        calculate_missing: CalculateMissingRecipeItems,
        open_external: Callable[[], AbstractContextManager[ExternalRecipes]],
    ) -> None:
        self._calculate_missing = calculate_missing
        self._open_external = open_external

    def get_missing_items(
        self, user_id: int, household_id: int, recipe_id: int, servings: int
    ) -> list[MissingRecipeItem]:
        shortfall = self._calculate_missing.execute(user_id, household_id, recipe_id, servings)
        return _to_missing_items(shortfall)

    def get_missing_external_items(
        self, user_id: int, household_id: int, reference: str
    ) -> list[MissingRecipeItem]:
        try:
            with self._open_external() as external:
                shortfall = external.calculate_shortfall.execute(user_id, household_id, reference)
        except RecipeNotFoundAtSourceError as error:
            raise ExternalRecipeNotFoundError from error
        except (RecipeSourceUnavailableError, RecipeSourceContractError) as error:
            raise RecipesUnavailableError from error
        return _to_missing_items(shortfall)


def _to_missing_items(shortfall: RecipeShortfall) -> list[MissingRecipeItem]:
    return [
        MissingRecipeItem(
            name=item.name,
            ingredient_id=item.ingredient_id,
            stocked_product_id=item.stocked_product_id,
            amount=item.amount,
            unit_code=item.unit_code,
        )
        for item in shortfall.missing_items
    ]
