from inventory.application.ports.product_nutrition_reader import ProductNutritionReader
from inventory.domain.models import InventoryItemListing, InventoryItemSnapshot
from shared.item_calories import count_item_calories


class InventoryCalorieCounter:
    def __init__(self, nutrition: ProductNutritionReader) -> None:
        self._nutrition = nutrition

    def count(self, item: InventoryItemSnapshot) -> InventoryItemListing:
        listings = self.count_many(item.household_id, [item])
        return listings[0]

    def count_many(
        self, household_id: int, items: list[InventoryItemSnapshot]
    ) -> list[InventoryItemListing]:
        product_ids = {item.product_id for item in items}
        nutrition = self._nutrition.find_product_nutrition(household_id, product_ids)
        listings: list[InventoryItemListing] = []
        for item in items:
            quantity = item.as_quantity()
            calories = count_item_calories(quantity, nutrition[item.product_id])
            listings.append(InventoryItemListing(item=item, calories=calories))
        return listings
