from dataclasses import dataclass
from decimal import Decimal

from catalog.domain.errors import InvalidTagCaloriesError
from catalog.domain.provenance import Provenance

MAX_KCAL_PER_100G = Decimal("900")
KCAL_DECIMAL_PLACES = 1
KCAL_MAX_DIGITS = 4
KCAL_STEP = Decimal(1).scaleb(-KCAL_DECIMAL_PLACES)


@dataclass(frozen=True, slots=True)
class TagCalories:
    kcal_per_100g: Decimal
    provenance: Provenance

    def __post_init__(self) -> None:
        if not Decimal(0) <= self.kcal_per_100g <= MAX_KCAL_PER_100G:
            raise InvalidTagCaloriesError(
                f"Calories per 100 g must lie between 0 and {MAX_KCAL_PER_100G}."
            )
        if self.kcal_per_100g != self.kcal_per_100g.quantize(KCAL_STEP):
            raise InvalidTagCaloriesError(
                f"Calories per 100 g carry at most {KCAL_DECIMAL_PLACES} decimal place."
            )

    @classmethod
    def manual(cls, kcal_per_100g: Decimal) -> TagCalories:
        provenance = Provenance.manual()
        return cls(kcal_per_100g=kcal_per_100g, provenance=provenance)

    @classmethod
    def from_reference(cls, kcal_per_100g: Decimal, reference_url: str) -> TagCalories:
        provenance = Provenance.from_reference(reference_url)
        return cls(kcal_per_100g=kcal_per_100g, provenance=provenance)


@dataclass(frozen=True, slots=True)
class CalorieReference:
    tag_name: str
    calories: TagCalories

    def __post_init__(self) -> None:
        if not self.calories.provenance.is_reference:
            raise InvalidTagCaloriesError("An imported value comes from a reference source.")
