from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from django.contrib.auth.models import Permission, User
from rest_framework.test import APIClient

from promotions.application.permissions import VIEW_PROMOTIONS_PERMISSION
from promotions.application.ports.promotion_source import (
    PromotionSource,
    PromotionSourceContractError,
    PromotionSourceUnavailable,
)
from promotions.presentation import views
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


def _use_source(monkeypatch: pytest.MonkeyPatch, source: PromotionSource) -> None:
    @contextmanager
    def factory() -> Iterator[PromotionSource]:
        yield source

    monkeypatch.setattr(views, "open_promotion_source", factory)


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
    _use_source(monkeypatch, FailingPromotionSource(PromotionSourceUnavailable("down")))
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
