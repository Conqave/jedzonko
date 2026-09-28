from inventory.application.use_cases.consume_inventory_quantity import ConsumeInventoryQuantity
from recipes.application.ports.inventory_consumer import HouseholdInventoryConsumer
from shared.measurement import Quantity


class InventoryConsumer(HouseholdInventoryConsumer):
    def __init__(self, consume: ConsumeInventoryQuantity) -> None:
        self._consume = consume

    def consume(self, household_id: int, product_id: int, quantity: Quantity) -> None:
        self._consume.execute(household_id, product_id, quantity.amount, quantity.unit)
