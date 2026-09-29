from dataclasses import replace

from catalog.application.errors import IngredientNotFoundError
from catalog.application.ports.ingredient_line_repository import IngredientLineRepository
from catalog.application.ports.ingredient_references import IngredientReferences
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.ports.product_classification_repository import (
    ProductClassificationRepository,
)
from catalog.domain.errors import IngredientMergeError
from catalog.domain.ingredient import Ingredient
from catalog.domain.merge import surviving_link
from shared.transactions import TransactionManager


class MergeIngredients:

    def __init__(
        self,
        ingredients: IngredientRepository,
        classifications: ProductClassificationRepository,
        references: tuple[IngredientReferences, ...],
        lines: IngredientLineRepository,
        transactions: TransactionManager,
    ) -> None:
        self._ingredients = ingredients
        self._classifications = classifications
        self._references = references
        self._lines = lines
        self._transactions = transactions

    def execute(self, source_id: int, target_id: int) -> Ingredient:
        if source_id == target_id:
            raise IngredientMergeError("An ingredient cannot be merged into itself.")
        with self._transactions.atomic():
            target = self._ingredients.find(target_id)
            if self._ingredients.find(source_id) is None or target is None:
                raise IngredientNotFoundError
            for link in self._classifications.list_links_to(source_id):
                classification = self._classifications.find(link.product_id)
                if classification is None:
                    raise AssertionError("A product link without its product.")
                existing = classification.find(target_id)
                self._classifications.delete(link.product_id, source_id)
                kept = link if existing is None else surviving_link(existing, link)
                self._classifications.save((replace(kept, ingredient_id=target_id),))
            for references in self._references:
                references.reassign(source_id, target_id)
            self._lines.reassign(source_id, target_id)
            self._ingredients.move_names_as_aliases(source_id, target_id)
            self._ingredients.delete(source_id)
            return target
