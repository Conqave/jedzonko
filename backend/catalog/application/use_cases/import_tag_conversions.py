from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.application.reference_import import (
    ReferenceImportLog,
    ReferenceImportRun,
    TagFact,
    find_referenced_tags,
)
from catalog.domain.conversions import ConversionReference, Density, PieceWeight
from catalog.domain.ingredient import Ingredient
from catalog.domain.provenance import ReferenceImportDecision, decide_reference_import
from shared.transactions import TransactionManager


class ImportTagConversions:
    def __init__(self, ingredients: IngredientRepository, transactions: TransactionManager) -> None:
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(self, references: tuple[ConversionReference, ...]) -> ReferenceImportRun:
        tag_names = tuple(reference.tag_name for reference in references)
        log = ReferenceImportLog()
        with self._transactions.atomic():
            tags = find_referenced_tags(self._ingredients, tag_names)
            for reference, tag in zip(references, tags, strict=True):
                if tag is None:
                    log.record_unknown(reference.tag_name)
                    continue
                if reference.piece_weight is not None:
                    self._apply_piece_weight(tag, reference.piece_weight, log)
                if reference.density is not None:
                    self._apply_density(tag, reference.density, log)
        return log.freeze()

    def _apply_piece_weight(
        self, tag: Ingredient, piece_weight: PieceWeight, log: ReferenceImportLog
    ) -> None:
        current = tag.piece_weight
        current_provenance = None if current is None else current.provenance
        is_unchanged = current == piece_weight
        decision = decide_reference_import(current_provenance, is_unchanged)
        if decision is ReferenceImportDecision.UPDATE:
            self._ingredients.save_piece_weight(tag.id, piece_weight)
        log.record(tag, TagFact.PIECE_WEIGHT, decision)

    def _apply_density(self, tag: Ingredient, density: Density, log: ReferenceImportLog) -> None:
        current = tag.density
        current_provenance = None if current is None else current.provenance
        is_unchanged = current == density
        decision = decide_reference_import(current_provenance, is_unchanged)
        if decision is ReferenceImportDecision.UPDATE:
            self._ingredients.save_density(tag.id, density)
        log.record(tag, TagFact.DENSITY, decision)
