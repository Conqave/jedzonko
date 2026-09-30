import re
from dataclasses import dataclass
from enum import IntEnum

from catalog.domain.ingredient import Ingredient
from shared.text import normalize_text


class NameMatchRank(IntEnum):
    EXACT = 0
    NAME_PREFIX = 1
    WORD_PREFIX = 2
    CONTAINS = 3


@dataclass(frozen=True, slots=True)
class IngredientNameMatch:
    ingredient: Ingredient
    normalized_name: str


def rank_name_match(normalized_name: str, normalized_query: str) -> NameMatchRank:
    if normalized_name == normalized_query:
        return NameMatchRank.EXACT
    if normalized_name.startswith(normalized_query):
        return NameMatchRank.NAME_PREFIX
    escaped_query = re.escape(normalized_query)
    if re.search(rf"(?<!\w){escaped_query}", normalized_name):
        return NameMatchRank.WORD_PREFIX
    if normalized_query in normalized_name:
        return NameMatchRank.CONTAINS
    raise AssertionError(f"{normalized_name!r} does not contain {normalized_query!r}.")


def rank_ingredients(matches: list[IngredientNameMatch], normalized_query: str) -> list[Ingredient]:
    ingredients: dict[int, Ingredient] = {}
    best_ranks: dict[int, NameMatchRank] = {}
    for match in matches:
        ingredient_id = match.ingredient.id
        rank = rank_name_match(match.normalized_name, normalized_query)
        known_rank = best_ranks.get(ingredient_id)
        if known_rank is None or rank < known_rank:
            best_ranks[ingredient_id] = rank
        ingredients[ingredient_id] = match.ingredient

    def ranking_key(ingredient_id: int) -> tuple[NameMatchRank, str, str, int]:
        ingredient = ingredients[ingredient_id]
        sortable_name = normalize_text(ingredient.name)
        return best_ranks[ingredient_id], sortable_name, ingredient.name, ingredient_id

    ranked_ids = sorted(ingredients, key=ranking_key)
    return [ingredients[ingredient_id] for ingredient_id in ranked_ids]
