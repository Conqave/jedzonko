from typing import TextIO

from catalog.domain.calories import CalorieReference, TagCalories
from catalog.domain.errors import InvalidFactProvenanceError, InvalidTagCaloriesError
from catalog.presentation.reference_file import (
    InvalidReferenceFileError,
    read_decimal,
    read_reference_rows,
    read_tag_name,
    read_url,
)

CALORIE_FILE_COLUMNS = ("tag", "kcal_per_100g", "source_url")


def read_calorie_references(stream: TextIO) -> tuple[CalorieReference, ...]:
    rows = read_reference_rows(stream, CALORIE_FILE_COLUMNS)
    return tuple(_to_reference(row, line_number) for line_number, row in rows)


def _to_reference(row: dict[str, str], line_number: int) -> CalorieReference:
    tag_name = read_tag_name(row["tag"], line_number)
    kcal_per_100g = read_decimal(row["kcal_per_100g"], line_number)
    reference_url = read_url(row["source_url"], line_number)
    try:
        calories = TagCalories.from_reference(kcal_per_100g, reference_url)
    except (InvalidTagCaloriesError, InvalidFactProvenanceError) as error:
        raise InvalidReferenceFileError(f"Line {line_number}: {error}") from error
    return CalorieReference(tag_name=tag_name, calories=calories)
