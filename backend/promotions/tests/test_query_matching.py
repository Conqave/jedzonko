import pytest

from promotions.domain.matching import matches_query


@pytest.mark.parametrize(
    "product_name",
    [
        "Twaróg półtłusty wiejski Piątnica",
        "Twarog polltusty",
        "Serek twarogowy Kids World Minecraft",
        "SERKI TWAROGOWE ZIARNISTE",
    ],
)
def test_word_prefix_matches_are_accepted(product_name: str) -> None:
    assert matches_query(product_name, "twaróg") is True


@pytest.mark.parametrize(
    "product_name",
    [
        "Krem do twarzy multi-odżywczy Eveline 24k Gold & Diamenty",
        "Serum do twarzy Eveline Glass Skin",
        "Podkład do twarzy Eveline Finish Show",
        "Szynka konserwowa wieprzowa Tarczyński",
        "Ser gouda w plastrach Światowid 1 kg",
    ],
)
def test_unrelated_products_are_rejected(product_name: str) -> None:
    assert matches_query(product_name, "twaróg") is False


def test_diacritics_are_ignored_on_both_sides() -> None:
    assert matches_query("Maslo extra Mlekovita", "masło") is True
    assert matches_query("Masło ekstra", "maslo") is True
    assert matches_query("Żurek śląski", "zurek") is True
    assert matches_query("Ćwikła z chrzanem", "cwikla") is True


def test_multi_token_query_requires_every_token_to_match() -> None:
    assert matches_query("Twaróg półtłusty Piątnica", "twaróg półtłusty") is True
    assert matches_query("Twaróg chudy Piątnica", "twaróg półtłusty") is False


def test_substring_only_occurrences_do_not_match() -> None:
    assert matches_query("Mleko UHT Łaciate", "ko") is False


def test_blank_query_never_matches() -> None:
    assert matches_query("Twaróg", "   ") is False
