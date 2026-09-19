from shared.text import normalize_text


def test_polish_diacritics_are_stripped() -> None:
    assert normalize_text("Mąka pszenna") == "maka pszenna"
    assert normalize_text("Żółć ĘŚĆŃŹ") == "zolc escnz"


def test_case_is_folded_and_whitespace_collapsed() -> None:
    assert normalize_text("  CUKIER   trzcinowy \n") == "cukier trzcinowy"


def test_a_more_specific_name_stays_a_different_product() -> None:
    assert normalize_text("Mąka pszenna") != normalize_text("Mąka pszenna typ 500")
