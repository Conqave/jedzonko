import csv
from decimal import Decimal, InvalidOperation
from typing import TextIO

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from catalog.domain.calories import CalorieReference, TagCalories
from catalog.domain.errors import InvalidTagCaloriesError

CALORIE_FILE_COLUMNS = ("tag", "kcal_per_100g", "source_url")

_URL_VALIDATOR = URLValidator(schemes=["http", "https"])


class InvalidCalorieReferenceFileError(Exception):
    pass


def read_calorie_references(stream: TextIO) -> tuple[CalorieReference, ...]:
    reader = csv.DictReader(stream)
    header = reader.fieldnames
    if header is None or tuple(header) != CALORIE_FILE_COLUMNS:
        expected = ",".join(CALORIE_FILE_COLUMNS)
        raise InvalidCalorieReferenceFileError(f"The header must be {expected}.")
    references: list[CalorieReference] = []
    for row in reader:
        reference = _to_reference(row, reader.line_num)
        references.append(reference)
    return tuple(references)


def _to_reference(row: dict[str, str], line_number: int) -> CalorieReference:
    values = [row.get(column) for column in CALORIE_FILE_COLUMNS]
    if None in row or None in values:
        raise InvalidCalorieReferenceFileError(
            f"Line {line_number} does not have exactly {len(CALORIE_FILE_COLUMNS)} columns."
        )
    tag_name = row["tag"].strip()
    if not tag_name:
        raise InvalidCalorieReferenceFileError(f"Line {line_number} has no tag name.")
    kcal_per_100g = _read_kcal(row["kcal_per_100g"], line_number)
    reference_url = _read_url(row["source_url"], line_number)
    try:
        calories = TagCalories.from_reference(kcal_per_100g, reference_url)
    except InvalidTagCaloriesError as error:
        raise InvalidCalorieReferenceFileError(f"Line {line_number}: {error}") from error
    return CalorieReference(tag_name=tag_name, calories=calories)


def _read_kcal(text: str, line_number: int) -> Decimal:
    decimal_text = text.strip().replace(",", ".")
    try:
        value = Decimal(decimal_text)
    except InvalidOperation as error:
        raise InvalidCalorieReferenceFileError(
            f"Line {line_number}: {text!r} is not a number."
        ) from error
    if not value.is_finite():
        raise InvalidCalorieReferenceFileError(f"Line {line_number}: {text!r} is not a number.")
    return value


def _read_url(text: str, line_number: int) -> str:
    url = text.strip()
    try:
        _URL_VALIDATOR(url)
    except ValidationError as error:
        raise InvalidCalorieReferenceFileError(
            f"Line {line_number}: {url!r} is not an http(s) URL."
        ) from error
    return url
