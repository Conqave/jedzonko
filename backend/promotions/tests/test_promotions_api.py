import pytest
from django.contrib.auth.models import Permission, User
from rest_framework.test import APIClient

from promotions.application.permissions import VIEW_PROMOTIONS_PERMISSION
from promotions.application.ports.promotion_source import (
    PromotionSource,
    PromotionSourceContractError,
    PromotionSourceUnavailableError,
)
from promotions.tests.fakes import FailingPromotionSource, FakePromotionSource, build_offer

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def normal_user() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


@pytest.fixture
def promotion_user() -> User:
    user = User.objects.create_user(username="ola", password="Ma-Psa-1234")
    app_label, codename = VIEW_PROMOTIONS_PERMISSION.split(".")
    user.user_permissions.add(
        Permission.objects.get(content_type__app_label=app_label, codename=codename)
    )
    return User.objects.get(pk=user.pk)


@pytest.fixture
def second_promotion_user() -> User:
    user = User.objects.create_user(username="ela", password="Ma-Rybe-1234")
    app_label, codename = VIEW_PROMOTIONS_PERMISSION.split(".")
    user.user_permissions.add(
        Permission.objects.get(content_type__app_label=app_label, codename=codename)
    )
    return User.objects.get(pk=user.pk)


def _use_source(monkeypatch: pytest.MonkeyPatch, source: PromotionSource) -> None:
    def provider(client: object, search_leaflet_limit: int) -> PromotionSource:
        return source

    monkeypatch.setattr("promotions.composition.BlixProvider", provider)


def test_search_is_denied_for_anonymous_caller(api_client: APIClient) -> None:
    response = api_client.get("/api/promotions/search/", {"query": "twaróg"})

    assert response.status_code == 403
    assert response.data["code"] == "not_authenticated"


def test_search_is_denied_without_promotion_permission(
    api_client: APIClient, normal_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({"twaróg": [build_offer("T", "Lidl", "h1")]}))
    api_client.force_login(normal_user)

    response = api_client.get("/api/promotions/search/", {"query": "twaróg"})

    assert response.status_code == 403
    assert response.data["code"] == "permission_denied"


def test_search_returns_offers_for_permitted_user(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(
        monkeypatch,
        FakePromotionSource({"twaróg": [build_offer("Twaróg", "Lidl", "h1", price="4.49")]}),
    )
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/search/", {"query": "twaróg"})

    assert response.status_code == 200
    assert response.data[0]["name"] == "Twaróg"
    assert response.data[0]["shop_name"] == "Lidl"
    assert response.data[0]["shop_slug"] == "lidl"
    assert response.data[0]["price"] == "4.49"
    assert response.data[0]["valid_until"] == "2026-09-20"


def test_search_requires_query_parameter(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/search/")

    assert response.status_code == 400
    assert response.data["code"] == "invalid"


def test_search_maps_provider_unavailable_to_service_unavailable(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FailingPromotionSource(PromotionSourceUnavailableError("down")))
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/search/", {"query": "twaróg"})

    assert response.status_code == 503
    assert response.data["code"] == "promotion_source_unavailable"


def test_search_maps_provider_contract_error_to_bad_gateway(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FailingPromotionSource(PromotionSourceContractError("changed")))
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/search/", {"query": "twaróg"})

    assert response.status_code == 502
    assert response.data["code"] == "promotion_source_contract_invalid"


def test_store_coverage_is_denied_without_promotion_permission(
    api_client: APIClient, normal_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(normal_user)

    response = api_client.post(
        "/api/promotions/store-coverage/", {"queries": ["twaróg"]}, format="json"
    )

    assert response.status_code == 403
    assert response.data["code"] == "permission_denied"


def test_store_coverage_returns_ranked_stores(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(
        monkeypatch,
        FakePromotionSource(
            {
                "twaróg": [
                    build_offer("Twaróg", "Biedronka", "h1"),
                    build_offer("Twaróg", "Lidl", "h2"),
                ],
                "masło": [build_offer("Masło", "Biedronka", "h3")],
            }
        ),
    )
    api_client.force_login(promotion_user)

    response = api_client.post(
        "/api/promotions/store-coverage/", {"queries": ["twaróg", "masło"]}, format="json"
    )

    assert response.status_code == 200
    assert [(item["shop_name"], item["matched_query_count"]) for item in response.data] == [
        ("Biedronka", 2),
        ("Lidl", 1),
    ]


def test_store_coverage_requires_at_least_one_query(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    response = api_client.post("/api/promotions/store-coverage/", {"queries": []}, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "invalid"


def test_shops_are_denied_without_promotion_permission(
    api_client: APIClient, normal_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(normal_user)

    response = api_client.get("/api/promotions/shops/")

    assert response.status_code == 403
    assert response.data["code"] == "permission_denied"


def test_shops_expose_name_slug_and_url(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/shops/")

    assert response.status_code == 200
    assert response.data == [
        {"name": "Biedronka", "slug": "biedronka", "url": "https://blix.pl/sklep/biedronka/"},
        {"name": "Carrefour", "slug": "carrefour", "url": "https://blix.pl/sklep/carrefour/"},
        {"name": "Lidl", "slug": "lidl", "url": "https://blix.pl/sklep/lidl/"},
    ]


def test_shops_map_provider_unavailable_to_service_unavailable(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FailingPromotionSource(PromotionSourceUnavailableError("down")))
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/shops/")

    assert response.status_code == 503
    assert response.data["code"] == "promotion_source_unavailable"


def test_search_forwards_repeated_shop_query_parameters(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Lidl", "h1"),
                build_offer("Twaróg", "Carrefour", "h2"),
            ]
        }
    )
    _use_source(monkeypatch, source)
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/search/?query=twar%C3%B3g&shop=lidl&shop=biedronka")

    assert response.status_code == 200
    assert source.received_shop_slugs == [("lidl", "biedronka")]
    assert [item["shop_slug"] for item in response.data] == ["lidl"]


def test_store_coverage_applies_the_requested_shop_selection(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "h1"),
                build_offer("Twaróg", "Lidl", "h2"),
            ],
            "masło": [build_offer("Masło", "Biedronka", "h3")],
        }
    )
    _use_source(monkeypatch, source)
    api_client.force_login(promotion_user)

    response = api_client.post(
        "/api/promotions/store-coverage/",
        {"queries": ["twaróg", "masło"], "shops": ["lidl"]},
        format="json",
    )

    assert response.status_code == 200
    assert [(item["shop_slug"], item["matched_query_count"]) for item in response.data] == [
        ("lidl", 1)
    ]


def test_favourite_shops_are_denied_without_promotion_permission(
    api_client: APIClient, normal_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(normal_user)

    assert api_client.get("/api/promotions/favourite-shops/").status_code == 403
    assert (
        api_client.put(
            "/api/promotions/favourite-shops/", {"shops": ["lidl"]}, format="json"
        ).status_code
        == 403
    )


def test_favourite_shops_are_empty_before_anything_is_saved(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    response = api_client.get("/api/promotions/favourite-shops/")

    assert response.status_code == 200
    assert response.data == []


def test_favourite_shops_round_trip_through_put_and_get(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    saved = api_client.put(
        "/api/promotions/favourite-shops/", {"shops": ["lidl", "biedronka"]}, format="json"
    )

    assert saved.status_code == 200
    assert saved.data == [
        {"name": "Biedronka", "slug": "biedronka"},
        {"name": "Lidl", "slug": "lidl"},
    ]
    assert api_client.get("/api/promotions/favourite-shops/").data == saved.data


def test_favourite_shops_put_replaces_the_whole_selection(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    api_client.put(
        "/api/promotions/favourite-shops/", {"shops": ["lidl", "biedronka"]}, format="json"
    )
    api_client.put("/api/promotions/favourite-shops/", {"shops": ["carrefour"]}, format="json")

    assert api_client.get("/api/promotions/favourite-shops/").data == [
        {"name": "Carrefour", "slug": "carrefour"}
    ]


def test_favourite_shops_put_accepts_an_empty_selection(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    api_client.put("/api/promotions/favourite-shops/", {"shops": ["lidl"]}, format="json")
    response = api_client.put("/api/promotions/favourite-shops/", {"shops": []}, format="json")

    assert response.status_code == 200
    assert response.data == []


def test_favourite_shops_put_rejects_unknown_shop_slugs(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))
    api_client.force_login(promotion_user)

    response = api_client.put(
        "/api/promotions/favourite-shops/", {"shops": ["biedornka"]}, format="json"
    )

    assert response.status_code == 400
    assert response.data["code"] == "unknown_shop"


def test_favourite_shops_are_isolated_per_user(
    api_client: APIClient,
    promotion_user: User,
    second_promotion_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _use_source(monkeypatch, FakePromotionSource({}))

    api_client.force_login(promotion_user)
    api_client.put("/api/promotions/favourite-shops/", {"shops": ["lidl"]}, format="json")
    api_client.logout()

    api_client.force_login(second_promotion_user)
    assert api_client.get("/api/promotions/favourite-shops/").data == []
    api_client.put("/api/promotions/favourite-shops/", {"shops": ["carrefour"]}, format="json")
    api_client.logout()

    api_client.force_login(promotion_user)
    assert api_client.get("/api/promotions/favourite-shops/").data == [
        {"name": "Lidl", "slug": "lidl"}
    ]


def test_store_coverage_falls_back_to_saved_favourites(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "h1"),
                build_offer("Twaróg", "Lidl", "h2"),
            ],
            "masło": [build_offer("Masło", "Biedronka", "h3")],
        }
    )
    _use_source(monkeypatch, source)
    api_client.force_login(promotion_user)
    api_client.put("/api/promotions/favourite-shops/", {"shops": ["lidl"]}, format="json")

    response = api_client.post(
        "/api/promotions/store-coverage/",
        {"queries": ["twaróg", "masło"]},
        format="json",
    )

    assert response.status_code == 200
    assert [(item["shop_slug"], item["matched_query_count"]) for item in response.data] == [
        ("lidl", 1)
    ]


def test_store_coverage_explicit_shops_override_saved_favourites(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "h1"),
                build_offer("Twaróg", "Lidl", "h2"),
            ]
        }
    )
    _use_source(monkeypatch, source)
    api_client.force_login(promotion_user)
    api_client.put("/api/promotions/favourite-shops/", {"shops": ["lidl"]}, format="json")

    response = api_client.post(
        "/api/promotions/store-coverage/",
        {"queries": ["twaróg"], "shops": ["biedronka"]},
        format="json",
    )

    assert [item["shop_slug"] for item in response.data] == ["biedronka"]


def test_store_coverage_uses_all_shops_without_favourites(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "h1"),
                build_offer("Twaróg", "Lidl", "h2"),
            ]
        }
    )
    _use_source(monkeypatch, source)
    api_client.force_login(promotion_user)

    response = api_client.post(
        "/api/promotions/store-coverage/", {"queries": ["twaróg"]}, format="json"
    )

    assert source.received_shop_slugs == [()]
    assert sorted(item["shop_slug"] for item in response.data) == ["biedronka", "lidl"]


def test_search_falls_back_to_saved_favourites(
    api_client: APIClient, promotion_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "h1"),
                build_offer("Twaróg", "Lidl", "h2"),
            ]
        }
    )
    _use_source(monkeypatch, source)
    api_client.force_login(promotion_user)
    api_client.put("/api/promotions/favourite-shops/", {"shops": ["lidl"]}, format="json")

    response = api_client.get("/api/promotions/search/", {"query": "twaróg"})

    assert source.received_shop_slugs == [("lidl",)]
    assert [item["shop_slug"] for item in response.data] == ["lidl"]
