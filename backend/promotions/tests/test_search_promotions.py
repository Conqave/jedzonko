import pytest

from promotions.application.use_cases.search_promotions import SearchPromotions
from promotions.tests.fakes import FakePromotionSource, build_offer


def test_search_promotions_returns_provider_offers() -> None:
    offer = build_offer("Twaróg półtłusty", "Biedronka", "hash-1")
    source = FakePromotionSource({"twaróg": [offer]})

    result = SearchPromotions(source).execute("twaróg")

    assert result == [offer]


def test_search_promotions_trims_query_before_calling_provider() -> None:
    source = FakePromotionSource({"twaróg": []})

    SearchPromotions(source).execute("  twaróg  ")

    assert source.received_queries == ["twaróg"]


def test_search_promotions_returns_empty_result_without_matches() -> None:
    source = FakePromotionSource({})

    assert SearchPromotions(source).execute("twaróg") == []


def test_search_promotions_rejects_blank_query() -> None:
    source = FakePromotionSource({})

    with pytest.raises(ValueError):
        SearchPromotions(source).execute("   ")
