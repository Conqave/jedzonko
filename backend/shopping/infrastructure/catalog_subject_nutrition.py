from catalog.application.use_cases.get_ingredients import GetIngredients
from catalog.application.use_cases.get_product_nutrition import GetProductNutrition
from catalog.domain.nutrition_facts import to_ingredient_nutrition
from shared.item_calories import SubjectNutrition
from shopping.application.ports.subject_nutrition_reader import SubjectNutritionReader


class CatalogSubjectNutrition(SubjectNutritionReader):
    def __init__(
        self, get_product_nutrition: GetProductNutrition, get_ingredients: GetIngredients
    ) -> None:
        self._get_product_nutrition = get_product_nutrition
        self._get_ingredients = get_ingredients

    def find_product_nutrition(
        self, household_id: int, product_ids: set[int]
    ) -> dict[int, SubjectNutrition]:
        return self._get_product_nutrition.execute(household_id, product_ids)

    def find_ingredient_nutrition(self, ingredient_ids: set[int]) -> dict[int, SubjectNutrition]:
        ingredients = self._get_ingredients.execute(ingredient_ids)
        return {
            ingredient_id: to_ingredient_nutrition(ingredient)
            for ingredient_id, ingredient in ingredients.items()
        }
