from catalog.application.errors import ProductNotFoundError
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager


class DeleteProductIngredient:
    def __init__(
        self,
        classifications: ProductClassificationRepository,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._classifications = classifications
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, product_id: int, ingredient_id: int) -> None:
        with self._transactions.atomic():
            classification = self._classifications.find(product_id)
            if classification is None:
                raise ProductNotFoundError
            require_membership(self._memberships, user_id, classification.household_id)
            forgotten = classification.forget(ingredient_id)
            self._classifications.delete(forgotten.product_id, forgotten.ingredient_id)
