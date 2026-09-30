import io
from decimal import Decimal

import pytest

from catalog.domain.calories import CalorieReference, TagCalories
from catalog.presentation.calorie_reference_file import read_calorie_references
from catalog.presentation.reference_file import InvalidReferenceFileError

HEADER = "tag,kcal_per_100g,source_url\n"


def _read(text: str) -> tuple[CalorieReference, ...]:
    stream = io.StringIO(text)
    return read_calorie_references(stream)


def test_rows_become_reference_calories() -> None:
    references = _read(
        HEADER + "jabłko,52,https://example.org/apple\n"
        '"mąka pszenna","364,5",http://example.org/flour\n'
    )

    assert references == (
        CalorieReference(
            tag_name="jabłko",
            calories=TagCalories.from_reference(Decimal("52"), "https://example.org/apple"),
        ),
        CalorieReference(
            tag_name="mąka pszenna",
            calories=TagCalories.from_reference(Decimal("364.5"), "http://example.org/flour"),
        ),
    )


@pytest.mark.parametrize(
    "text",
    [
        "name,kcal,url\njabłko,52,https://example.org/apple\n",
        HEADER + "jabłko,52\n",
        HEADER + "jabłko,52,https://example.org/apple,extra\n",
        HEADER + ",52,https://example.org/apple\n",
        HEADER + "jabłko,dużo,https://example.org/apple\n",
        HEADER + "jabłko,NaN,https://example.org/apple\n",
        HEADER + "jabłko,1200,https://example.org/apple\n",
        HEADER + "jabłko,52.25,https://example.org/apple\n",
        HEADER + "jabłko,52,ftp://example.org/apple\n",
        HEADER + "jabłko,52,\n",
        "",
    ],
)
def test_a_malformed_file_is_refused_whole(text: str) -> None:
    with pytest.raises(InvalidReferenceFileError):
        _read(text)
