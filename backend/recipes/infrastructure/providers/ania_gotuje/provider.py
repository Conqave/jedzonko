import json

import httpx

from recipes.application.ports.recipe_source import (
    RecipeNotFoundAtSourceError,
    RecipeSource,
    RecipeSourceContractError,
    RecipeSourceUnavailable,
)
from recipes.domain.external import ExternalRecipeDetail, ExternalRecipePage
from recipes.infrastructure.providers.ania_gotuje.mapper import AniaGotujeRecipeMapper

_REQUEST_HEADERS = {"Accept": "application/json", "Referer": "https://aniagotuje.pl/"}

# The search endpoint answers 403 with an empty body unless both `page` and
# `sort` are present, which is how the site's own client always calls it.
_SEARCH_SORT = "score,desc"


class AniaGotujeProvider(RecipeSource):
    base_url = "https://api.aniagotuje.pl"

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self._mapper = AniaGotujeRecipeMapper()

    def get_recipe(self, reference: str) -> ExternalRecipeDetail:
        slug = reference.strip()
        if not slug:
            raise ValueError("reference must not be empty")
        payload = self._get_json(f"{self.base_url}/client/post/{slug}")
        return self._mapper.map_detail(payload)

    def search_recipes(
        self,
        query: str,
        ingredient_names: tuple[str, ...],
        excluded_ingredient_names: tuple[str, ...],
        page: int,
        page_size: int,
    ) -> ExternalRecipePage:
        if page < 0:
            raise ValueError("page must not be negative")
        if page_size < 1:
            raise ValueError("page_size must be at least 1")
        params = {"page": str(page), "perPage": str(page_size), "sort": _SEARCH_SORT}
        normalized_query = query.strip()
        if normalized_query:
            params["query"] = normalized_query
        if ingredient_names:
            params["ing"] = ",".join(ingredient_names)
        if excluded_ingredient_names:
            params["exIng"] = ",".join(excluded_ingredient_names)
        payload = self._get_json(f"{self.base_url}/client/posts/search", params)
        return self._mapper.map_page(payload)

    def _get_json(self, url: str, params: dict[str, str] | None = None) -> object:
        try:
            response = self._client.get(url, params=params, headers=_REQUEST_HEADERS)
        except httpx.HTTPError as error:
            raise RecipeSourceUnavailable(f"Ania Gotuje request failed: {url}") from error
        if response.status_code == httpx.codes.NOT_FOUND:
            raise RecipeNotFoundAtSourceError(f"Ania Gotuje has no resource at {url}")
        if response.status_code >= httpx.codes.BAD_REQUEST:
            raise RecipeSourceUnavailable(f"Ania Gotuje responded {response.status_code} for {url}")
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RecipeSourceContractError(
                f"Ania Gotuje response is not valid JSON: {url}"
            ) from error
