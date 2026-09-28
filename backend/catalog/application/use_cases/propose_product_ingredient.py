from datetime import datetime

from catalog.application.errors import IngredientNotFoundError, ProductNotFoundError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.domain.product_ingredient import ProductIngredient
from shared.transactions import TransactionManager


class ProposeProductIngredient:
    def __init__(
        self,
        classifications: ProductClassificationRepository,
        ingredients: IngredientRepository,
        transactions: TransactionManager,
    ) -> None:
        self._classifications = classifications
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(
        self, product_id: int, ingredient_id: int, model_name: str, now: datetime
    ) -> ProductIngredient:
        with self._transactions.atomic():
            classification = self._classifications.find(product_id)
            if classification is None:
                raise ProductNotFoundError
            if self._ingredients.find(ingredient_id) is None:
                raise IngredientNotFoundError
            proposal = classification.propose(ingredient_id, model_name, now)
            self._classifications.save((proposal,))
            return proposal
