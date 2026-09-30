from decimal import Decimal
from typing import TextIO

from catalog.domain.conversions import ConversionReference, Density, PieceWeight
from catalog.domain.errors import (
    InvalidConversionReferenceError,
    InvalidDensityError,
    InvalidFactProvenanceError,
    InvalidPieceWeightError,
)
from catalog.presentation.reference_file import (
    InvalidReferenceFileError,
    find_decimal,
    read_reference_rows,
    read_tag_name,
    read_url,
)

CONVERSION_FILE_COLUMNS = ("tag", "grams_per_piece", "grams_per_ml", "source_url")


def read_conversion_references(stream: TextIO) -> tuple[ConversionReference, ...]:
    rows = read_reference_rows(stream, CONVERSION_FILE_COLUMNS)
    return tuple(_to_reference(row, line_number) for line_number, row in rows)


def _to_reference(row: dict[str, str], line_number: int) -> ConversionReference:
    tag_name = read_tag_name(row["tag"], line_number)
    grams_per_piece = find_decimal(row["grams_per_piece"], line_number)
    grams_per_ml = find_decimal(row["grams_per_ml"], line_number)
    reference_url = read_url(row["source_url"], line_number)
    try:
        piece_weight = _to_piece_weight(grams_per_piece, reference_url)
        density = _to_density(grams_per_ml, reference_url)
        return ConversionReference(tag_name=tag_name, piece_weight=piece_weight, density=density)
    except (
        InvalidPieceWeightError,
        InvalidDensityError,
        InvalidFactProvenanceError,
        InvalidConversionReferenceError,
    ) as error:
        raise InvalidReferenceFileError(f"Line {line_number}: {error}") from error


def _to_piece_weight(grams_per_piece: Decimal | None, reference_url: str) -> PieceWeight | None:
    if grams_per_piece is None:
        return None
    return PieceWeight.from_reference(grams_per_piece, reference_url)


def _to_density(grams_per_ml: Decimal | None, reference_url: str) -> Density | None:
    if grams_per_ml is None:
        return None
    return Density.from_reference(grams_per_ml, reference_url)
