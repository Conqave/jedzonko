from pathlib import Path

import httpx
import pytest

from recipes.application.errors import (
    RecipeNotFoundAtSourceError,
    RecipeSourceContractError,
    RecipeSourceUnavailableError,
)
from recipes.infrastructure.providers.ania_gotuje.site import AniaGotujeSite, CrawlPacing

FIXTURES = Path(__file__).parent / "fixtures"
SITEMAP = (FIXTURES / "ania_sitemap.xml").read_text(encoding="utf-8")
PAGE = (FIXTURES / "ania_recipe_page_omlet.html").read_text(encoding="utf-8")
IMAGE_URL = "https://cdn.aniagotuje.com/pictures/articles/omlet-testowy.jpg"


ROBOTS_URL = "https://aniagotuje.pl/robots.txt"


def _site(
    responses: list[httpx.Response],
    sleeps: list[float],
    attempts: int = 3,
    robots: str | None = None,
) -> tuple[AniaGotujeSite, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def handle_request(request: httpx.Request) -> httpx.Response:
        if str(request.url) == ROBOTS_URL:
            return httpx.Response(404) if robots is None else httpx.Response(200, text=robots)
        requests.append(request)
        return responses.pop(0)

    client = httpx.Client(transport=httpx.MockTransport(handle_request))
    pacing = CrawlPacing(delay_seconds=1.5, attempts=attempts)
    return AniaGotujeSite(client, pacing, sleeps.append), requests


def test_references_come_from_recipe_pages_of_the_site_map() -> None:
    site, requests = _site([httpx.Response(200, text=SITEMAP)], [])

    references = site.list_recipe_references()

    assert str(requests[0].url) == "https://aniagotuje.pl/sitemap.xml"
    assert references == ("omlet-testowy", "zupa-testowa")


def test_a_site_map_index_is_refused() -> None:
    index = '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>'
    site, _ = _site([httpx.Response(200, text=index)], [])

    with pytest.raises(RecipeSourceContractError):
        site.list_recipe_references()


def test_recipe_page_is_read_from_its_own_microdata() -> None:
    site, requests = _site([httpx.Response(200, text=PAGE)], [])

    recipe = site.fetch_recipe("omlet-testowy")

    assert str(requests[0].url) == "https://aniagotuje.pl/przepis/omlet-testowy"
    assert recipe.name == "Omlet testowy"
    assert recipe.source_url == "https://aniagotuje.pl/przepis/omlet-testowy"
    assert recipe.image_source_url == IMAGE_URL
    assert recipe.yield_label == "2 porcje"
    assert [line.source_text for line in recipe.ingredients] == [
        "3 jajka - 165 g",
        "pół szklanki mleka",
        "szczypta soli",
    ]
    assert recipe.ingredients[0].name == "3 jajka"
    assert recipe.ingredients[0].unit_code == "g"


def test_a_page_without_ingredients_is_refused() -> None:
    page = '<article itemscope itemtype="https://schema.org/Recipe"><h1 itemprop="name">X</h1></article>'
    site, _ = _site([httpx.Response(200, text=page)], [])

    with pytest.raises(RecipeSourceContractError):
        site.fetch_recipe("x")


def test_every_request_waits_and_transient_failures_back_off() -> None:
    sleeps: list[float] = []
    responses = [httpx.Response(503), httpx.Response(429), httpx.Response(200, text=PAGE)]
    site, requests = _site(responses, sleeps)

    site.fetch_recipe("omlet-testowy")

    assert len(requests) == 3
    assert sleeps == [1.5, 1.5, 3.0, 6.0]


def test_retries_end_with_an_unavailable_source() -> None:
    site, requests = _site([httpx.Response(500), httpx.Response(502)], [], attempts=2)

    with pytest.raises(RecipeSourceUnavailableError):
        site.fetch_recipe("omlet-testowy")
    assert len(requests) == 2


def test_a_missing_page_is_not_retried() -> None:
    site, requests = _site([httpx.Response(404)], [])

    with pytest.raises(RecipeNotFoundAtSourceError):
        site.fetch_recipe("nie-ma")
    assert len(requests) == 1


def test_image_is_downloaded_with_a_file_name_from_the_reference() -> None:
    response = httpx.Response(200, content=b"\xff\xd8jpeg", headers={"Content-Type": "image/jpeg"})
    site, _ = _site([response], [])

    image = site.fetch_image("omlet-testowy", IMAGE_URL)

    assert image.filename == "omlet-testowy.jpg"
    assert image.content == b"\xff\xd8jpeg"


def test_a_non_image_response_is_refused() -> None:
    response = httpx.Response(200, text="<html/>", headers={"Content-Type": "text/html"})
    site, _ = _site([response], [])

    with pytest.raises(RecipeSourceContractError):
        site.fetch_image("omlet-testowy", IMAGE_URL)


def test_pacing_keeps_at_least_one_second_between_requests() -> None:
    with pytest.raises(ValueError):
        CrawlPacing(delay_seconds=0.5, attempts=3)


def test_pages_disallowed_by_robots_are_not_requested() -> None:
    robots = "User-agent: *\nDisallow: /przepis/\n"
    site, requests = _site([], [], robots=robots)

    with pytest.raises(RecipeSourceContractError):
        site.fetch_recipe("omlet-testowy")
    assert requests == []


def test_robots_of_the_site_do_not_apply_to_image_hosts() -> None:
    robots = "User-agent: *\nDisallow: /\n"
    response = httpx.Response(200, content=b"\xff\xd8jpeg", headers={"Content-Type": "image/jpeg"})
    site, requests = _site([response], [], robots=robots)

    site.fetch_image("omlet-testowy", IMAGE_URL)

    assert [str(request.url) for request in requests] == [IMAGE_URL]
