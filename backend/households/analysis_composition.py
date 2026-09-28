from collections.abc import Iterator
from contextlib import contextmanager

import httpx
from django.conf import settings

from households.application.ports.ingredient_matcher import IngredientMatcher
from households.application.ports.recipe_requirement_reader import RecipeRequirementReader
from households.application.use_cases.analyze_unmatched_ingredients import (
    AnalyzeUnmatchedIngredients,
)
from households.composition import (
    build_alias_proposal_repository,
    build_household_repository,
    build_product_repository,
)
from households.infrastructure.providers.ollama.matcher import OllamaIngredientMatcher
from households.infrastructure.recipes_recipe_requirement_reader import (
    RecipesRecipeRequirementReader,
)


def build_recipe_requirement_reader() -> RecipeRequirementReader:
    return RecipesRecipeRequirementReader()


def _resolve_reasoning_effort(effort: str) -> str | bool:
    if effort == "true":
        return True
    if effort == "false":
        return False
    return effort


@contextmanager
def open_ingredient_matcher() -> Iterator[IngredientMatcher]:
    with httpx.Client(timeout=httpx.Timeout(settings.ALIAS_MATCHER_HTTP_TIMEOUT_SECONDS)) as client:
        yield OllamaIngredientMatcher(
            client,
            settings.ALIAS_MATCHER_BASE_URL,
            settings.ALIAS_MATCHER_MODEL,
            _resolve_reasoning_effort(settings.ALIAS_MATCHER_REASONING_EFFORT),
        )


def build_analyze_unmatched_ingredients(
    matcher: IngredientMatcher,
) -> AnalyzeUnmatchedIngredients:
    return AnalyzeUnmatchedIngredients(
        build_household_repository(),
        build_product_repository(),
        build_recipe_requirement_reader(),
        build_alias_proposal_repository(),
        matcher,
        settings.ALIAS_ANALYSIS_QUESTION_LIMIT,
    )
