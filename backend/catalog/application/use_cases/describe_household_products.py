from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.product import ProductIdentity, ProductTag


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
        tagged_ids = {ingredient_id for ids in confirmed.values() for ingredient_id in ids}
        ingredients = self._ingredients.find_many(tagged_ids)
        identities: dict[int, ProductIdentity] = {}
        for product in self._products.list_for_household(household_id):
            tags = tuple(
                ProductTag(ingredient_id=ingredient_id, name=ingredients[ingredient_id].name)
                for ingredient_id in confirmed.get(product.id, ())
            )
            identities[product.id] = ProductIdentity(
                product_id=product.id, name=product.name, tags=tags, package=product.package
            )
        return identities
