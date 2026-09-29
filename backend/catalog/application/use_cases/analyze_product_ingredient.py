from datetime import datetime

from catalog.application.classification_candidates import find_undecided_candidate_ids
from catalog.application.errors import IngredientClassifierContractError, ProductNotFoundError
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.errors import ProductAlreadyClassifiedError
from catalog.domain.product_ingredient import ProductIngredient
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager


class AnalyzeProductIngredient:
    def __init__(
        self,
        products: ProductRepository,
        ingredients: IngredientRepository,
        classifications: ProductClassificationRepository,
        classifier: IngredientClassifier,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._products = products
        self._ingredients = ingredients
        self._classifications = classifications
        self._classifier = classifier
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, product_id: int, now: datetime) -> ProductIngredient | None:
        product = self._products.find(product_id)
        classification = self._classifications.find(product_id)
        if product is None or classification is None:
            raise ProductNotFoundError
        require_membership(self._memberships, user_id, classification.household_id)
        if classification.confirmed() is not None:
            raise ProductAlreadyClassifiedError
        names = self._ingredients.list_names()
        candidate_ids = find_undecided_candidate_ids(product.name, names, classification)
        if not candidate_ids:
            return None
        candidates = self._ingredients.find_many(set(candidate_ids))
        candidate_names = tuple(candidates[each].name for each in candidate_ids)
        choice = self._classifier.find_matching_ingredient(product.name, candidate_names)
        if choice is None:
            return None
        if not 0 <= choice < len(candidate_ids):
            raise IngredientClassifierContractError(f"Choice {choice} is not a candidate.")
        proposal = classification.propose(candidate_ids[choice], self._classifier.model_name, now)
        with self._transactions.atomic():
            self._classifications.save((proposal,))
        return proposal
