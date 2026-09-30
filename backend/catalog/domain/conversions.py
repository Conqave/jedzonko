from dataclasses import dataclass
from decimal import Decimal

from catalog.domain.errors import (
    InvalidConversionReferenceError,
    InvalidDensityError,
    InvalidPieceWeightError,
)
from catalog.domain.provenance import Provenance

MAX_GRAMS_PER_PIECE = Decimal("10000")
GRAMS_PER_PIECE_DECIMAL_PLACES = 1
GRAMS_PER_PIECE_MAX_DIGITS = 6
GRAMS_PER_PIECE_STEP = Decimal(1).scaleb(-GRAMS_PER_PIECE_DECIMAL_PLACES)

MAX_GRAMS_PER_ML = Decimal("3")
GRAMS_PER_ML_DECIMAL_PLACES = 3
GRAMS_PER_ML_MAX_DIGITS = 4
GRAMS_PER_ML_STEP = Decimal(1).scaleb(-GRAMS_PER_ML_DECIMAL_PLACES)


@dataclass(frozen=True, slots=True)
class PieceWeight:
    grams_per_piece: Decimal
    provenance: Provenance

    def __post_init__(self) -> None:
        if not Decimal(0) < self.grams_per_piece <= MAX_GRAMS_PER_PIECE:
            raise InvalidPieceWeightError(
                f"A piece weighs more than 0 g and at most {MAX_GRAMS_PER_PIECE} g."
            )
        if self.grams_per_piece != self.grams_per_piece.quantize(GRAMS_PER_PIECE_STEP):
            raise InvalidPieceWeightError(
                f"Grams per piece carry at most {GRAMS_PER_PIECE_DECIMAL_PLACES} decimal place."
            )

    @classmethod
    def manual(cls, grams_per_piece: Decimal) -> PieceWeight:
        provenance = Provenance.manual()
        return cls(grams_per_piece=grams_per_piece, provenance=provenance)

    @classmethod
    def from_reference(cls, grams_per_piece: Decimal, reference_url: str) -> PieceWeight:
        provenance = Provenance.from_reference(reference_url)
        return cls(grams_per_piece=grams_per_piece, provenance=provenance)


@dataclass(frozen=True, slots=True)
class Density:
    grams_per_ml: Decimal
    provenance: Provenance

    def __post_init__(self) -> None:
        if not Decimal(0) < self.grams_per_ml <= MAX_GRAMS_PER_ML:
            raise InvalidDensityError(
                f"A density lies above 0 and at most {MAX_GRAMS_PER_ML} g/ml."
            )
        if self.grams_per_ml != self.grams_per_ml.quantize(GRAMS_PER_ML_STEP):
            raise InvalidDensityError(
                f"A density carries at most {GRAMS_PER_ML_DECIMAL_PLACES} decimal places."
            )

    @classmethod
    def manual(cls, grams_per_ml: Decimal) -> Density:
        provenance = Provenance.manual()
        return cls(grams_per_ml=grams_per_ml, provenance=provenance)

    @classmethod
    def from_reference(cls, grams_per_ml: Decimal, reference_url: str) -> Density:
        provenance = Provenance.from_reference(reference_url)
        return cls(grams_per_ml=grams_per_ml, provenance=provenance)


@dataclass(frozen=True, slots=True)
class ConversionReference:
    tag_name: str
    piece_weight: PieceWeight | None
    density: Density | None

    def __post_init__(self) -> None:
        if self.piece_weight is None and self.density is None:
            raise InvalidConversionReferenceError(
                f"The reference for {self.tag_name!r} provides no conversion."
            )
        if self.piece_weight is not None and not self.piece_weight.provenance.is_reference:
            raise InvalidConversionReferenceError("An imported value comes from a reference.")
        if self.density is not None and not self.density.provenance.is_reference:
            raise InvalidConversionReferenceError("An imported value comes from a reference.")
