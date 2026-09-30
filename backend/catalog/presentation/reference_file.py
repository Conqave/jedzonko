import csv
from decimal import Decimal, InvalidOperation
from typing import TextIO

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

_URL_VALIDATOR = URLValidator(schemes=["http", "https"])


class InvalidReferenceFileError(Exception):
    pass


def read_reference_rows(
    stream: TextIO, columns: tuple[str, ...]
) -> tuple[tuple[int, dict[str, str]], ...]:
    reader = csv.DictReader(stream)
    header = reader.fieldnames
    if header is None or tuple(header) != columns:
        expected = ",".join(columns)
        raise InvalidReferenceFileError(f"The header must be {expected}.")
    rows: list[tuple[int, dict[str, str]]] = []
    for row in reader:
        values = [row.get(column) for column in columns]
        if None in row or None in values:
            raise InvalidReferenceFileError(
                f"Line {reader.line_num} does not have exactly {len(columns)} columns."
            )
        rows.append((reader.line_num, row))
    return tuple(rows)


def read_tag_name(text: str, line_number: int) -> str:
    tag_name = text.strip()
    if not tag_name:
        raise InvalidReferenceFileError(f"Line {line_number} has no tag name.")
    return tag_name


def read_decimal(text: str, line_number: int) -> Decimal:
    decimal_text = text.strip().replace(",", ".")
    try:
        value = Decimal(decimal_text)
    except InvalidOperation as error:
        raise InvalidReferenceFileError(f"Line {line_number}: {text!r} is not a number.") from error
    if not value.is_finite():
        raise InvalidReferenceFileError(f"Line {line_number}: {text!r} is not a number.")
    return value


def find_decimal(text: str, line_number: int) -> Decimal | None:
    if not text.strip():
        return None
    return read_decimal(text, line_number)


def read_url(text: str, line_number: int) -> str:
    url = text.strip()
    try:
        _URL_VALIDATOR(url)
    except ValidationError as error:
        raise InvalidReferenceFileError(
            f"Line {line_number}: {url!r} is not an http(s) URL."
        ) from error
    return url
