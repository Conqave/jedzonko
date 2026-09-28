from datetime import datetime

from catalog.application.errors import (
    IngredientNotFoundError,
    NotAHouseholdMemberError,
    ProductNotFoundError,
)
from catalog.application.ports.household_membership_reader import HouseholdMembershipReader
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.transaction_manager import TransactionManager
from catalog.domain.product_ingredient import ProductIngredient


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
            if not self._memberships.is_member(user_id, classification.household_id):
                raise NotAHouseholdMemberError
            if self._ingredients.find(ingredient_id) is None:
                raise IngredientNotFoundError
            changes = classification.confirm(ingredient_id, now)
            self._classifications.save(changes)
            confirmed = classification.apply(changes).confirmed()
            if confirmed is None:
                raise AssertionError("Confirming left the product without a confirmed ingredient.")
            return confirmed
