from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from catalog.domain.errors import InvalidTagCaloriesError

MAX_KCAL_PER_100G = Decimal("900")
KCAL_DECIMAL_PLACES = 1
KCAL_MAX_DIGITS = 4
MAX_REFERENCE_URL_LENGTH = 500
KCAL_STEP = Decimal(1).scaleb(-KCAL_DECIMAL_PLACES)


class CalorieSource(StrEnum):
    MANUAL = "manual"
    REFERENCE = "reference"


@dataclass(frozen=True, slots=True)
class TagCalories:
    kcal_per_100g: Decimal
    source: CalorieSource
    reference_url: str | None

    def __post_init__(self) -> None:
        if not Decimal(0) <= self.kcal_per_100g <= MAX_KCAL_PER_100G:
            raise InvalidTagCaloriesError(
                f"Calories per 100 g must lie between 0 and {MAX_KCAL_PER_100G}."
            )
        if self.kcal_per_100g != self.kcal_per_100g.quantize(KCAL_STEP):
            raise InvalidTagCaloriesError(
                f"Calories per 100 g carry at most {KCAL_DECIMAL_PLACES} decimal place."
            )
        has_reference = self.reference_url is not None
        if has_reference is not (self.source is CalorieSource.REFERENCE):
            raise InvalidTagCaloriesError("Exactly the reference values carry a source URL.")
        if self.reference_url is not None and not self.reference_url.strip():
            raise InvalidTagCaloriesError("The source URL is empty.")
        if self.reference_url is not None and len(self.reference_url) > MAX_REFERENCE_URL_LENGTH:
            raise InvalidTagCaloriesError(
                f"The source URL is longer than {MAX_REFERENCE_URL_LENGTH} characters."
            )

    @classmethod
    def manual(cls, kcal_per_100g: Decimal) -> TagCalories:
        return cls(kcal_per_100g=kcal_per_100g, source=CalorieSource.MANUAL, reference_url=None)

    @classmethod
    def from_reference(cls, kcal_per_100g: Decimal, reference_url: str) -> TagCalories:
        return cls(
            kcal_per_100g=kcal_per_100g,
            source=CalorieSource.REFERENCE,
            reference_url=reference_url,
        )

    @property
    def is_manual(self) -> bool:
        return self.source is CalorieSource.MANUAL


@dataclass(frozen=True, slots=True)
class CalorieReference:
    tag_name: str
    calories: TagCalories

    def __post_init__(self) -> None:
        if self.calories.source is not CalorieSource.REFERENCE:
            raise InvalidTagCaloriesError("An imported value comes from a reference source.")
