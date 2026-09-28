from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from recipes.application.errors import (
    RecipeNotFoundAtSourceError,
    RecipeSourceContractError,
    RecipeSourceUnavailableError,
)
from recipes.infrastructure.providers.ania_gotuje.provider import AniaGotujeProvider

FIXTURES = Path(__file__).parent / "fixtures"
NALESNIKI = (FIXTURES / "ania_post_nalesniki.json").read_text(encoding="utf-8")
SERNIK = (FIXTURES / "ania_post_sernik_krolewski.json").read_text(encoding="utf-8")
SEARCH = (FIXTURES / "ania_search_nalesniki.json").read_text(encoding="utf-8")
SEARCH_BY_INGREDIENTS = (FIXTURES / "ania_search_by_ingredients.json").read_text(encoding="utf-8")
SEARCH_EMPTY = (FIXTURES / "ania_search_empty.json").read_text(encoding="utf-8")

BODIES = {
    "/client/post/jak-zrobic-ciasto-na-nalesniki": NALESNIKI,
    "/client/post/sernik-krolewski": SERNIK,
    "/client/posts/search": SEARCH,
}


def build_provider(
    requests: list[httpx.Request], status_code: int = 200, body: str | None = None
) -> AniaGotujeProvider:
    def handle_request(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if status_code != 200:
            return httpx.Response(status_code, text="", request=request)
        text = BODIES[request.url.path] if body is None else body
        return httpx.Response(
            200, text=text, headers={"Content-Type": "application/json"}, request=request
        )

    return AniaGotujeProvider(httpx.Client(transport=httpx.MockTransport(handle_request)))


def test_get_recipe_maps_the_provider_payload_with_attribution() -> None:
    requests: list[httpx.Request] = []
    provider = build_provider(requests)

    recipe = provider.get_recipe("jak-zrobic-ciasto-na-nalesniki")

    assert requests[0].url.path == "/client/post/jak-zrobic-ciasto-na-nalesniki"
    assert requests[0].headers["referer"] == "https://aniagotuje.pl/"
    assert recipe.summary.source_name == "Ania Gotuje"
    assert recipe.summary.reference == "jak-zrobic-ciasto-na-nalesniki"
    assert (
        recipe.summary.source_url == "https://aniagotuje.pl/przepis/jak-zrobic-ciasto-na-nalesniki"
    )
    assert recipe.summary.image_url is not None
    assert recipe.summary.image_url.startswith("https://cdn.aniagotuje.com/")
    assert recipe.summary.name == "Naleśniki"
    assert recipe.summary.yield_label == "do 16 naleśników średnicy 24 cm"
    assert recipe.preparation_time_minutes == 5
    assert recipe.cooking_time_minutes == 25
    assert recipe.summary.tag_names == ("dla dzieci", "jajka")


def test_get_recipe_reduces_html_to_plain_text() -> None:
    provider = build_provider([])

    recipe = provider.get_recipe("jak-zrobic-ciasto-na-nalesniki")

    assert "<" not in recipe.summary.description
    assert recipe.summary.description.startswith(
        "Poznaj najlepszy i sprawdzony przepis na naleśniki"
    )
    assert recipe.steps
    assert all("<" not in step for step in recipe.steps)
    assert recipe.steps[0].startswith("Szklanka ma u mnie pojemność 250 ml.")


def test_get_recipe_parses_quantities_only_from_the_unambiguous_trailing_form() -> None:
    provider = build_provider([])

    recipe = provider.get_recipe("jak-zrobic-ciasto-na-nalesniki")
    measured = {
        item.name: (item.quantity, item.unit_code)
        for item in recipe.ingredients
        if item.quantity is not None
    }

    assert measured == {
        "1 pełna szklanka i 2 łyżki mąki pszennej": (Decimal("230"), "g"),
        "1 szklanka mleka": (Decimal("250"), "ml"),
        "1 szklanka wody": (Decimal("250"), "ml"),
    }


def test_get_recipe_keeps_unmeasurable_ingredients_with_their_text() -> None:
    provider = build_provider([])

    recipe = provider.get_recipe("jak-zrobic-ciasto-na-nalesniki")
    unmeasured = [item for item in recipe.ingredients if item.quantity is None]

    assert [item.name for item in unmeasured] == [
        "3 średnie jajka - około 165 g po rozbiciu",
        "4 łyżki oleju roślinnego - około 40 ml",
        "szczypta soli",
    ]
    assert all(item.source_text == item.name for item in unmeasured)
    assert all(item.unit_code is None for item in unmeasured)


def test_get_recipe_flattens_multiple_ingredient_groups() -> None:
    provider = build_provider([])

    recipe = provider.get_recipe("sernik-krolewski")

    assert len(recipe.ingredients) == 12
    assert recipe.ingredients[0].name == "2,5 szklanki mąki pszennej"
    assert recipe.ingredients[0].quantity == Decimal("400")
    assert recipe.ingredients[6].name == "1 kg mielonego twarogu np. z kubełka"
    assert recipe.ingredients[6].quantity is None
    assert recipe.cooking_time_minutes == 60


def test_empty_reference_is_rejected() -> None:
    provider = build_provider([])

    with pytest.raises(ValueError):
        provider.get_recipe("   ")


def test_missing_recipe_is_reported_as_not_found_at_source() -> None:
    provider = build_provider([], status_code=404)

    with pytest.raises(RecipeNotFoundAtSourceError):
        provider.get_recipe("nie-ma-takiego-przepisu")


def test_server_error_is_reported_as_unavailable() -> None:
    provider = build_provider([], status_code=503)

    with pytest.raises(RecipeSourceUnavailableError):
        provider.get_recipe("jak-zrobic-ciasto-na-nalesniki")


def test_transport_error_is_reported_as_unavailable() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    provider = AniaGotujeProvider(httpx.Client(transport=httpx.MockTransport(handle_request)))

    with pytest.raises(RecipeSourceUnavailableError):
        provider.get_recipe("jak-zrobic-ciasto-na-nalesniki")


def test_non_json_response_is_reported_as_a_contract_error() -> None:
    provider = build_provider([], body="<html>nope</html>")

    with pytest.raises(RecipeSourceContractError):
        provider.get_recipe("jak-zrobic-ciasto-na-nalesniki")


def test_payload_without_ingredients_is_reported_as_a_contract_error() -> None:
    provider = build_provider([], body='{"id": 1, "slug": "x", "ingredients": []}')

    with pytest.raises(RecipeSourceContractError):
        provider.get_recipe("x")


def test_search_always_sends_the_page_and_sort_parameters_the_endpoint_requires() -> None:
    requests: list[httpx.Request] = []
    provider = build_provider(requests)

    provider.search_recipes("naleśniki", (), (), 0, 3)

    assert requests[0].url.path == "/client/posts/search"
    assert requests[0].url.params["page"] == "0"
    assert requests[0].url.params["sort"] == "score,desc"
    assert requests[0].url.params["perPage"] == "3"
    assert requests[0].url.params["query"] == "naleśniki"


def test_search_maps_the_envelope_and_every_entry_with_attribution() -> None:
    provider = build_provider([])

    page = provider.search_recipes("naleśniki", (), (), 0, 3)

    assert (page.page, page.page_size, page.total_count, page.total_pages) == (0, 3, 252, 84)
    assert len(page.recipes) == 3
    first = page.recipes[0]
    assert first.source_name == "Ania Gotuje"
    assert first.source_url == f"https://aniagotuje.pl/przepis/{first.reference}"
    assert first.reference == "omlet-twarogowy-z-jablkami"
    assert first.name == "Omlet twarogowy z jabłkami"
    assert first.total_time_minutes == 30
    assert "<" not in first.description
    assert "jajko" in first.tag_names


def test_search_sends_ingredient_filters_as_comma_separated_tag_names() -> None:
    requests: list[httpx.Request] = []
    provider = build_provider(requests, body=SEARCH_BY_INGREDIENTS)

    page = provider.search_recipes("", ("jajko", "mąka pszenna"), ("mleko",), 0, 3)

    assert requests[0].url.params["ing"] == "jajko,mąka pszenna"
    assert requests[0].url.params["exIng"] == "mleko"
    assert "query" not in requests[0].url.params
    assert page.total_count == 549


def test_search_without_matches_yields_an_empty_page() -> None:
    provider = build_provider([], body=SEARCH_EMPTY)

    page = provider.search_recipes("nic-takiego", (), (), 0, 12)

    assert page.recipes == ()
    assert page.total_count == 0


def test_search_rejects_a_negative_page() -> None:
    provider = build_provider([])

    with pytest.raises(ValueError):
        provider.search_recipes("x", (), (), -1, 12)


def test_search_rejects_an_empty_page_size() -> None:
    provider = build_provider([])

    with pytest.raises(ValueError):
        provider.search_recipes("x", (), (), 0, 0)


def test_search_envelope_without_content_is_a_contract_error() -> None:
    provider = build_provider([], body='{"number": 0, "size": 12}')

    with pytest.raises(RecipeSourceContractError):
        provider.search_recipes("x", (), (), 0, 12)
