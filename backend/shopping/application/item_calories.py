from shared.item_calories import SubjectNutrition, count_item_calories
from shared.measurement import Quantity
from shopping.application.ports.subject_nutrition_reader import SubjectNutritionReader
from shopping.domain.shopping_item_listing import ShoppingItemListing
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class ShoppingCalorieCounter:
    def __init__(self, nutrition: SubjectNutritionReader) -> None:
        self._nutrition = nutrition

    def count(self, household_id: int, item: ShoppingItemSnapshot) -> ShoppingItemListing:
        listings = self.count_many(household_id, [item])
        return listings[0]

    def count_many(
        self, household_id: int, items: list[ShoppingItemSnapshot]
    ) -> list[ShoppingItemListing]:
        product_ids = {
            item.subject.product_id for item in items if item.subject.product_id is not None
        }
        ingredient_ids = {
            item.subject.ingredient_id for item in items if item.subject.ingredient_id is not None
        }
        products = self._nutrition.find_product_nutrition(household_id, product_ids)
        ingredients = self._nutrition.find_ingredient_nutrition(ingredient_ids)
        listings: list[ShoppingItemListing] = []
        for item in items:
            nutrition = _find_nutrition(item, products, ingredients)
            quantity = None if item.unit is None else Quantity(amount=item.quantity, unit=item.unit)
            calories = count_item_calories(quantity, nutrition)
            listings.append(ShoppingItemListing(item=item, calories=calories))
        return listings


def _find_nutrition(
    item: ShoppingItemSnapshot,
    products: dict[int, SubjectNutrition],
    ingredients: dict[int, SubjectNutrition],
) -> SubjectNutrition:
    subject = item.subject
    if subject.product_id is not None:
        return products[subject.product_id]
    if subject.ingredient_id is not None:
        return ingredients[subject.ingredient_id]
    return SubjectNutrition.untagged()
