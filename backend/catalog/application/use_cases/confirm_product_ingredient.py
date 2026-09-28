from datetime import datetime

from catalog.application.errors import (
    IngredientNotFoundError,
    ProductNotFoundError,
)
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.domain.product_ingredient import ProductIngredient
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager


class ConfirmProductIngredient:
    def __init__(
        self,
        classifications: ProductClassificationRepository,
        ingredients: IngredientRepository,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._classifications = classifications
        self._ingredients = ingredients
        self._memberships = memberships
        self._transactions = transactions

    def execute(
        self, user_id: int, product_id: int, ingredient_id: int, now: datetime
    ) -> ProductIngredient:
        with self._transactions.atomic():
            classification = self._classifications.find(product_id)
            if classification is None:
                raise ProductNotFoundError
            require_membership(self._memberships, user_id, classification.household_id)
            if self._ingredients.find(ingredient_id) is None:
                raise IngredientNotFoundError
            changes = classification.confirm(ingredient_id, now)
            self._classifications.save(changes)
            confirmed = classification.apply(changes).confirmed()
            if confirmed is None:
                raise AssertionError("Confirming left the product without a confirmed ingredient.")
            return confirmed
