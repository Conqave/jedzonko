from dataclasses import dataclass
from datetime import datetime

from catalog.application.classification_candidates import find_undecided_tags
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
from catalog.domain.product_ingredient import ProductIngredient
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class ClassificationRun:
    question_count: int
    question_limit: int
    proposals: tuple[ProductIngredient, ...]
    skipped: tuple[str, ...]
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
        skipped: list[str] = []
        asked = 0
        for product in self._products.list_unclassified():
            if asked >= self._question_limit:
                break
            classification = self._classifications.find(product.id)
            if classification is None or classification.confirmed():
                continue
            tags = find_undecided_tags(names, classification)
            if not tags:
                continue
            asked += 1
            tag_names = tuple(tag.name for tag in tags)
            try:
                choices = self._classifier.find_matching_tags(product.name, tag_names)
            except IngredientClassifierContractError as error:
                skipped.append(f"{product.name}: {error}")
                continue
            except IngredientClassifierError as error:
                return ClassificationRun(
                    asked, self._question_limit, tuple(proposals), tuple(skipped), str(error)
                )
            if any(not 0 <= choice < len(tags) for choice in choices):
                skipped.append(f"{product.name}: choices {choices} are not all tags")
                continue
            chosen_ids = sorted({tags[choice].id for choice in choices})
            product_proposals = tuple(
                classification.assign_from_model(ingredient_id, self._classifier.model_name, now)
                for ingredient_id in chosen_ids
            )
            if not dry_run:
                with self._transactions.atomic():
                    self._classifications.save(product_proposals)
            proposals.extend(product_proposals)
        return ClassificationRun(
            asked, self._question_limit, tuple(proposals), tuple(skipped), None
        )
