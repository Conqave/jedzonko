import pytest

from promotions.application.use_cases.compare_store_promotion_coverage import (
    CompareStorePromotionCoverage,
)
from promotions.tests.fakes import FakePromotionSource, build_offer


def test_coverage_ranks_stores_by_number_of_matched_requested_items() -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Biedronka", "hash-1"),
                build_offer("Twaróg wiejski", "Lidl", "hash-2"),
            ],
            "masło": [build_offer("Masło extra", "Biedronka", "hash-3")],
        }
    )

    coverage = CompareStorePromotionCoverage(source).execute(["twaróg", "masło"])

    assert [(item.shop_name, item.matched_query_count) for item in coverage] == [
        ("Biedronka", 2),
        ("Lidl", 1),
    ]
    assert coverage[0].matched_queries == ("twaróg", "masło")
    assert len(coverage[0].offers) == 2


def test_coverage_counts_each_requested_item_once_per_store() -> None:
    source = FakePromotionSource(
        {
            "twaróg": [
                build_offer("Twaróg", "Lidl", "hash-1"),
                build_offer("Twaróg light", "Lidl", "hash-2"),
            ]
        }
    )

    coverage = CompareStorePromotionCoverage(source).execute(["twaróg"])

    assert coverage[0].matched_query_count == 1
    assert len(coverage[0].offers) == 2


def test_coverage_deduplicates_requested_items() -> None:
    source = FakePromotionSource({"twaróg": [build_offer("Twaróg", "Lidl", "hash-1")]})

    CompareStorePromotionCoverage(source).execute(["twaróg", " twaróg "])

    assert source.received_queries == ["twaróg"]


def test_coverage_is_empty_when_no_store_has_matches() -> None:
    source = FakePromotionSource({})

    assert CompareStorePromotionCoverage(source).execute(["twaróg"]) == []


def test_coverage_rejects_blank_requested_item() -> None:
    source = FakePromotionSource({})

    with pytest.raises(ValueError):
        CompareStorePromotionCoverage(source).execute(["twaróg", "  "])
