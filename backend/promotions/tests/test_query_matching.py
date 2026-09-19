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
    assert matches_query(product_name, None, "twaróg") is True


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
    assert matches_query(product_name, None, "twaróg") is False


def test_diacritics_are_ignored_on_both_sides() -> None:
    assert matches_query("Maslo extra Mlekovita", None, "masło") is True
    assert matches_query("Masło ekstra", None, "maslo") is True
    assert matches_query("Żurek śląski", None, "zurek") is True
    assert matches_query("Ćwikła z chrzanem", None, "cwikla") is True


def test_multi_token_query_requires_every_token_to_match() -> None:
    assert matches_query("Twaróg półtłusty Piątnica", None, "twaróg półtłusty") is True
    assert matches_query("Twaróg chudy Piątnica", None, "twaróg półtłusty") is False


def test_substring_only_occurrences_do_not_match() -> None:
    assert matches_query("Mleko UHT Łaciate", None, "ko") is False


def test_blank_query_never_matches() -> None:
    assert matches_query("Twaróg", None, "   ") is False


def test_product_name_still_matches_when_brand_is_present() -> None:
    assert matches_query("Mleko UHT 3,2% Mlekovita", "Mlekovita", "mleko") is True


@pytest.mark.parametrize(
    "product_name",
    [
        "Masło ekstra Polskie Mlekovita",
        "Skyr pitny owoce ogrodowe Mlekovita",
    ],
)
def test_brand_words_inside_the_name_do_not_match(product_name: str) -> None:
    assert matches_query(product_name, "Mlekovita", "mleko") is False


@pytest.mark.parametrize(
    "product_name",
    [
        "Masło ekstra Polskie Mlekovita",
        "Skyr pitny owoce ogrodowe Mlekovita",
        "Mleko UHT 3,2% Mlekovita",
    ],
)
def test_brand_name_is_not_searchable(product_name: str) -> None:
    assert matches_query(product_name, "Mlekovita", "mlekovita") is False


def test_offer_without_brand_behaves_as_before() -> None:
    assert matches_query("Masło ekstra Polskie Mlekovita", None, "mleko") is True
    assert matches_query("Masło ekstra Polskie Mlekovita", None, "mlekovita") is True


def test_brand_removal_is_per_whole_word() -> None:
    assert matches_query("Mleko UHT Mlekovita", "Mlekovita", "mlekovita") is False
    assert matches_query("Mlekovita", "Mlekovita", "mleko") is False
