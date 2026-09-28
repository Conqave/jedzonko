from dataclasses import dataclass
from datetime import datetime

from catalog.application.errors import (
    IngredientClassifierContractError,
    IngredientClassifierError,
)
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.candidate_selection import select_classification_candidates
from catalog.domain.names import CatalogName
from catalog.domain.product_ingredient import ProductIngredient
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class ClassificationRun:
    question_count: int
    question_limit: int
    proposals: tuple[ProductIngredient, ...]
    failure: str | None


class ProposeIngredientsForProducts:

    def __init__(
        self,
        products: ProductRepository,
        ingredients: IngredientRepository,
        classifications: ProductClassificationRepository,
        classifier: IngredientClassifier,
        transactions: TransactionManager,
        question_limit: int,
    ) -> None:
        if question_limit < 1:
            raise ValueError("question_limit must be at least 1")
        self._products = products
        self._ingredients = ingredients
        self._classifications = classifications
        self._classifier = classifier
        self._transactions = transactions
        self._question_limit = question_limit

    def execute(self, now: datetime, dry_run: bool) -> ClassificationRun:
        names = self._ingredients.list_names()
        proposals: list[ProductIngredient] = []
        asked = 0
        for product in self._products.list_unclassified():
            if asked >= self._question_limit:
                break
            classification = self._classifications.find(product.id)
            if classification is None or classification.confirmed() is not None:
                continue
            candidate_ids = [
                ingredient_id
                for ingredient_id in select_classification_candidates(
                    CatalogName.parse(product.name).normalized_name, names
                )
                if classification.find(ingredient_id) is None
            ]
            if not candidate_ids:
                continue
            candidates = self._ingredients.find_many(set(candidate_ids))
            asked += 1
            try:
                choice = self._classifier.find_matching_ingredient(
                    product.name, tuple(candidates[each].name for each in candidate_ids)
                )
            except IngredientClassifierError as error:
                return ClassificationRun(asked, self._question_limit, tuple(proposals), str(error))
            if choice is None:
                continue
            if not 0 <= choice < len(candidate_ids):
                failure = IngredientClassifierContractError(f"Choice {choice} is not a candidate.")
                return ClassificationRun(
                    asked, self._question_limit, tuple(proposals), str(failure)
                )
            proposal = classification.propose(
                candidate_ids[choice], self._classifier.model_name, now
            )
            if not dry_run:
                with self._transactions.atomic():
                    self._classifications.save((proposal,))
            proposals.append(proposal)
        return ClassificationRun(asked, self._question_limit, tuple(proposals), None)
