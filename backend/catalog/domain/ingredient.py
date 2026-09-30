from dataclasses import dataclass
from enum import StrEnum

from catalog.domain.calories import TagCalories
from catalog.domain.conversions import Density, PieceWeight


class IngredientNameKind(StrEnum):
    CANONICAL = "canonical"
    ALIAS = "alias"


class IngredientNameSource(StrEnum):
    MANUAL = "manual"
    ANIA_GOTUJE = "ania_gotuje"


@dataclass(frozen=True, slots=True)
class Ingredient:
    id: int
    name: str
    calories: TagCalories | None
    piece_weight: PieceWeight | None
    density: Density | None


@dataclass(frozen=True, slots=True)
class IngredientName:
    ingredient_id: int
    name: str
    normalized_name: str
    kind: IngredientNameKind
    source: IngredientNameSource
