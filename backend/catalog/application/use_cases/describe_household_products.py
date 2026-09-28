from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.product import ProductIdentity


class DescribeHouseholdProducts:

    def __init__(
        self,
        products: ProductRepository,
        classifications: ProductClassificationRepository,
        ingredients: IngredientRepository,
    ) -> None:
        self._products = products
        self._classifications = classifications
        self._ingredients = ingredients

    def execute(self, household_id: int) -> dict[int, ProductIdentity]:
        confirmed = self._classifications.list_confirmed(household_id)
        ingredients = self._ingredients.find_many(set(confirmed.values()))
        identities: dict[int, ProductIdentity] = {}
        for product in self._products.list_for_household(household_id):
            ingredient_id = confirmed.get(product.id)
            ingredient = None if ingredient_id is None else ingredients[ingredient_id]
            identities[product.id] = ProductIdentity(
                product_id=product.id,
                name=product.name,
                ingredient_id=ingredient_id,
                ingredient_name=None if ingredient is None else ingredient.name,
                package=product.package,
            )
        return identities
