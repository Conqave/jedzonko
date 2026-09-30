from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.reference_import import (
    ReferenceImportLog,
    ReferenceImportRun,
    TagFact,
    find_referenced_tags,
)
from catalog.domain.calories import CalorieReference
from catalog.domain.ingredient import Ingredient
from catalog.domain.provenance import ReferenceImportDecision, decide_reference_import
from shared.transactions import TransactionManager


class ImportTagCalories:
    def __init__(self, ingredients: IngredientRepository, transactions: TransactionManager) -> None:
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(self, references: tuple[CalorieReference, ...]) -> ReferenceImportRun:
        tag_names = tuple(reference.tag_name for reference in references)
        log = ReferenceImportLog()
        with self._transactions.atomic():
            tags = find_referenced_tags(self._ingredients, tag_names)
            for reference, tag in zip(references, tags, strict=True):
                if tag is None:
                    log.record_unknown(reference.tag_name)
                    continue
                self._apply(tag, reference, log)
        return log.freeze()

    def _apply(self, tag: Ingredient, reference: CalorieReference, log: ReferenceImportLog) -> None:
        current = tag.calories
        current_provenance = None if current is None else current.provenance
        is_unchanged = current == reference.calories
        decision = decide_reference_import(current_provenance, is_unchanged)
        if decision is ReferenceImportDecision.UPDATE:
            self._ingredients.save_calories(tag.id, reference.calories)
        log.record(tag, TagFact.CALORIES, decision)
