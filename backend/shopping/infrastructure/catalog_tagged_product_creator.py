from datetime import datetime

from catalog.application.errors import DuplicateProductError
from catalog.application.use_cases.confirm_product_ingredient import ConfirmProductIngredient
from catalog.application.use_cases.create_product import CreateProduct
from shopping.application.errors import TagProductNameTakenError
from shopping.application.ports.tagged_product_creator import TaggedProductCreator


class CatalogTaggedProductCreator(TaggedProductCreator):
    def __init__(
        self, create_product: CreateProduct, confirm_ingredient: ConfirmProductIngredient
    ) -> None:
        self._create_product = create_product
        self._confirm_ingredient = confirm_ingredient

    def create_tagged_product(
        self,
        user_id: int,
        household_id: int,
        ingredient_id: int,
        name: str,
        unit_code: str,
        now: datetime,
    ) -> int:
        try:
            product = self._create_product.execute(
                user_id, household_id, name, unit_code, True, None
            )
        except DuplicateProductError as error:
            raise TagProductNameTakenError from error
        self._confirm_ingredient.execute(user_id, product.id, ingredient_id, now)
        return product.id
