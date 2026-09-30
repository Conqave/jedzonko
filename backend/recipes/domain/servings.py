import re
import unicodedata

_DASH_CATEGORY = "Pd"
_SERVING_UNITS = (
    r"porcja|porcje|porcję|porcji|osoba|osoby|osobę|osób|sztuka|sztuki|sztukę|sztuk|szt"
)
_SERVINGS_PATTERN = re.compile(
    rf"(?<![\d.,])(?:(?P<range_start>\d+)\s*-\s*)?(?P<count>\d+)\s+"
    rf"(?:[^\W\d_]+\s+)?(?:{_SERVING_UNITS})\b",
    re.IGNORECASE,
)


def read_servings(yield_label: str | None) -> int | None:
    if yield_label is None:
        return None
    label = _with_plain_dashes(yield_label)
    match = _SERVINGS_PATTERN.search(label)
    if match is None or match.group("range_start") is not None:
        return None
    count = int(match.group("count"))
    return count if count >= 1 else None


def _with_plain_dashes(text: str) -> str:
    characters = [
        "-" if unicodedata.category(character) == _DASH_CATEGORY else character
        for character in text
    ]
    return "".join(characters)
