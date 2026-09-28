from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from shared.measurement import MeasurementUnit
from shopping.domain.shopping_item_status import ShoppingItemStatus
from shopping.domain.shopping_subject import ShoppingSubject


@dataclass(frozen=True, slots=True)
class ShoppingItemSnapshot:
    id: int
    list_id: int
    subject: ShoppingSubject
    name: str
    quantity: Decimal
    unit: MeasurementUnit | None
    status: ShoppingItemStatus
    purchased_at: datetime | None

    @property
    def is_purchased(self) -> bool:
        return self.status is ShoppingItemStatus.PURCHASED
