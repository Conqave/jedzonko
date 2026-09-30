from collections.abc import Callable
from dataclasses import dataclass
from urllib.robotparser import RobotFileParser

import httpx

from recipes.application.errors import (
    RecipeNotFoundAtSourceError,
    RecipeSourceContractError,
    RecipeSourceUnavailableError,
)
from recipes.application.ports.recipe_site import RecipeSite
from recipes.domain.external import ImportedExternalRecipe, RecipeImage
from recipes.infrastructure.providers.ania_gotuje.mapper import RECIPE_PAGE_BASE_URL
from recipes.infrastructure.providers.ania_gotuje.recipe_page import read_recipe_page
from recipes.infrastructure.providers.ania_gotuje.sitemap import read_recipe_references

_SITE_HOST = "aniagotuje.pl"
_ROBOTS_URL = f"https://{_SITE_HOST}/robots.txt"
_ROBOTS_HEADERS = {"Accept": "text/plain"}
_PAGE_HEADERS = {"Accept": "text/html,application/xml"}
_IMAGE_HEADERS = {"Accept": "image/jpeg,image/png,image/webp"}
_IMAGE_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
_MAX_IMAGE_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class CrawlPacing:
    delay_seconds: float
    attempts: int

    def __post_init__(self) -> None:
        if self.delay_seconds < 1:
            raise ValueError("delay_seconds must be at least one second")
        if self.attempts < 1:
            raise ValueError("attempts must be at least 1")


class _TransientResponseError(Exception):
    pass


class AniaGotujeSite(RecipeSite):
    sitemap_url = f"https://{_SITE_HOST}/sitemap.xml"

    def __init__(
        self, client: httpx.Client, pacing: CrawlPacing, sleep: Callable[[float], None]
    ) -> None:
        self._client = client
        self._pacing = pacing
        self._sleep = sleep
        self._robots: RobotFileParser | None = None

    def list_recipe_references(self) -> tuple[str, ...]:
        response = self._get(self.sitemap_url, _PAGE_HEADERS)
        return read_recipe_references(response.text)

    def fetch_recipe(self, reference: str) -> ImportedExternalRecipe:
        slug = reference.strip()
        if not slug:
            raise ValueError("reference must not be empty")
        response = self._get(f"{RECIPE_PAGE_BASE_URL}/{slug}", _PAGE_HEADERS)
        return read_recipe_page(response.text, slug)

    def fetch_image(self, reference: str, url: str) -> RecipeImage:
        response = self._get(url, _IMAGE_HEADERS)
        content_type = response.headers.get("Content-Type", "")
        media_type = content_type.split(";")[0].strip().casefold()
        extension = _IMAGE_EXTENSIONS.get(media_type)
        if extension is None:
            raise RecipeSourceContractError(f"Image {url} has content type {content_type!r}.")
        content = response.content
        if not content or len(content) > _MAX_IMAGE_BYTES:
            raise RecipeSourceContractError(f"Image {url} has {len(content)} bytes.")
        return RecipeImage(filename=f"{reference.strip()}.{extension}", content=content)

    def _get(self, url: str, headers: dict[str, str]) -> httpx.Response:
        self._require_allowed(url)
        return self._get_paced(url, headers)

    def _require_allowed(self, url: str) -> None:
        if httpx.URL(url).host != _SITE_HOST:
            return
        robots = self._load_robots()
        user_agent = self._client.headers["User-Agent"]
        if not robots.can_fetch(user_agent, url):
            raise RecipeSourceContractError(f"robots.txt of Ania Gotuje disallows {url}")

    def _load_robots(self) -> RobotFileParser:
        if self._robots is None:
            self._robots = self._read_robots()
        return self._robots

    def _read_robots(self) -> RobotFileParser:
        robots = RobotFileParser()
        try:
            response = self._get_paced(_ROBOTS_URL, _ROBOTS_HEADERS)
        except RecipeNotFoundAtSourceError:
            robots.parse([])
            return robots
        lines = response.text.splitlines()
        robots.parse(lines)
        return robots

    def _get_paced(self, url: str, headers: dict[str, str]) -> httpx.Response:
        delay = self._pacing.delay_seconds
        attempt = 1
        while True:
            self._sleep(delay)
            try:
                return self._request(url, headers)
            except _TransientResponseError as failure:
                if attempt >= self._pacing.attempts:
                    raise RecipeSourceUnavailableError(str(failure)) from failure
            attempt += 1
            delay *= 2

    def _request(self, url: str, headers: dict[str, str]) -> httpx.Response:
        try:
            response = self._client.get(url, headers=headers)
        except httpx.TransportError as error:
            raise _TransientResponseError(f"Ania Gotuje request failed: {url}") from error
        status = response.status_code
        if status == httpx.codes.NOT_FOUND:
            raise RecipeNotFoundAtSourceError(f"Ania Gotuje has no page at {url}")
        if status == httpx.codes.TOO_MANY_REQUESTS or status >= httpx.codes.INTERNAL_SERVER_ERROR:
            raise _TransientResponseError(f"Ania Gotuje responded {status} for {url}")
        if status >= httpx.codes.BAD_REQUEST:
            raise RecipeSourceUnavailableError(f"Ania Gotuje responded {status} for {url}")
        return response
