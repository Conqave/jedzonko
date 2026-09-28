from datetime import datetime

from catalog.application.errors import ProductNotFoundError
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.domain.product_ingredient import ProductIngredient
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager


class RejectProductIngredient:
    def __init__(
        self,
        classifications: ProductClassificationRepository,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._classifications = classifications
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
            rejection = classification.reject(ingredient_id, now)
            self._classifications.save((rejection,))
            return rejection
