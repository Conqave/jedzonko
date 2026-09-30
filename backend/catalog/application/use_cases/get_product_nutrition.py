from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.use_cases.describe_household_products import DescribeHouseholdProducts
from catalog.domain.nutrition_facts import find_product_nutrition
from shared.item_calories import SubjectNutrition


class GetProductNutrition:
    def __init__(
        self, describe_products: DescribeHouseholdProducts, ingredients: IngredientRepository
    ) -> None:
        self._describe_products = describe_products
        self._ingredients = ingredients

    def execute(self, household_id: int, product_ids: set[int]) -> dict[int, SubjectNutrition]:
        if not product_ids:
            return {}
        identities = self._describe_products.execute(household_id)
        requested = {product_id: identities[product_id] for product_id in product_ids}
        tag_ids = {tag.ingredient_id for identity in requested.values() for tag in identity.tags}
        ingredients = self._ingredients.find_many(tag_ids)
        return {
            product_id: find_product_nutrition(identity, ingredients)
            for product_id, identity in requested.items()
        }
