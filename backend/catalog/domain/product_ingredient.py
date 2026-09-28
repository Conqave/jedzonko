from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from catalog.domain.errors import InvalidProductIngredientError


class ProductIngredientStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ProductIngredientSource(StrEnum):
    MANUAL = "manual"
    MODEL = "model"
    LEGACY = "legacy"


@dataclass(frozen=True, slots=True)
class ProductIngredient:
    product_id: int
    ingredient_id: int
    status: ProductIngredientStatus
    source: ProductIngredientSource
    model_name: str | None
    proposed_at: datetime | None
    decided_at: datetime | None

    def __post_init__(self) -> None:
        if (self.source is ProductIngredientSource.MODEL) != (self.model_name is not None):
            raise InvalidProductIngredientError(
                "A model name is required exactly when a model proposed the ingredient."
            )
        if self.source is ProductIngredientSource.MODEL and self.proposed_at is None:
            raise InvalidProductIngredientError("A model proposal needs its proposal time.")
        is_decided = self.status is not ProductIngredientStatus.PROPOSED
        if is_decided != (self.decided_at is not None):
            raise InvalidProductIngredientError(
                "A decision time is required exactly when the proposal was decided."
            )
