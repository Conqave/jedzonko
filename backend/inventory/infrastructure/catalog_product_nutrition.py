from catalog.application.use_cases.get_product_nutrition import GetProductNutrition
from inventory.application.ports.product_nutrition_reader import ProductNutritionReader
from shared.item_calories import SubjectNutrition


class CatalogProductNutrition(ProductNutritionReader):
    def __init__(self, get_product_nutrition: GetProductNutrition) -> None:
        self._get_product_nutrition = get_product_nutrition

    def find_product_nutrition(
        self, household_id: int, product_ids: set[int]
    ) -> dict[int, SubjectNutrition]:
        return self._get_product_nutrition.execute(household_id, product_ids)
