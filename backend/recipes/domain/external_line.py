from dataclasses import dataclass
from decimal import Decimal

MAX_LINE_TEXT_LENGTH = 255


@dataclass(frozen=True, slots=True)
class IngredientChoice:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class LineInterpretation:
    ingredient_id: int | None
    quantity: Decimal | None
    unit_code: str | None

    def __post_init__(self) -> None:
        if (self.quantity is None) != (self.unit_code is None):
            raise ValueError("A line amount has both a quantity and a unit, or neither.")
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("A line quantity is positive.")
