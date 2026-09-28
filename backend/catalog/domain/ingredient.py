from dataclasses import dataclass
from enum import StrEnum


class IngredientNameKind(StrEnum):
    CANONICAL = "canonical"
    ALIAS = "alias"


class IngredientNameSource(StrEnum):
    MANUAL = "manual"
    ANIA_GOTUJE = "ania_gotuje"
    LEGACY = "legacy"


@dataclass(frozen=True, slots=True)
class Ingredient:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class IngredientName:
    ingredient_id: int
    name: str
    normalized_name: str
    kind: IngredientNameKind
    source: IngredientNameSource
