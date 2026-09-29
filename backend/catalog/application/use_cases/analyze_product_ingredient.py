from datetime import datetime

from catalog.application.classification_candidates import find_undecided_tags
from catalog.application.errors import IngredientClassifierContractError, ProductNotFoundError
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.product_repository import ProductRepository
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

    def execute(
        self, user_id: int, product_id: int, now: datetime
    ) -> tuple[ProductIngredient, ...]:
        product = self._products.find(product_id)
        classification = self._classifications.find(product_id)
        if product is None or classification is None:
            raise ProductNotFoundError
        require_membership(self._memberships, user_id, classification.household_id)
        names = self._ingredients.list_names()
        tags = find_undecided_tags(names, classification)
        if not tags:
            return ()
        tag_names = tuple(tag.name for tag in tags)
        choices = self._classifier.find_matching_tags(product.name, tag_names)
        if any(not 0 <= choice < len(tags) for choice in choices):
            raise IngredientClassifierContractError(f"Choices {choices} are not all tags.")
        chosen_ids = sorted({tags[choice].id for choice in choices})
        proposals = tuple(
            classification.propose(ingredient_id, self._classifier.model_name, now)
            for ingredient_id in chosen_ids
        )
        with self._transactions.atomic():
            self._classifications.save(proposals)
        return proposals
