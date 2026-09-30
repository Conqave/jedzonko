from inventory.application.ports.product_nutrition_reader import ProductNutritionReader
from shared.item_calories import SubjectNutrition


class FakeProductNutritionReader(ProductNutritionReader):
    def __init__(self, nutrition: dict[int, SubjectNutrition]) -> None:
        self._nutrition = nutrition
        self.lookups: list[tuple[int, set[int]]] = []

    def find_product_nutrition(
        self, household_id: int, product_ids: set[int]
    ) -> dict[int, SubjectNutrition]:
        self.lookups.append((household_id, product_ids))
        return {product_id: self._nutrition[product_id] for product_id in product_ids}
