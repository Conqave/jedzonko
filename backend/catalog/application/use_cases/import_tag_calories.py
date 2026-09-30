from dataclasses import dataclass

from catalog.application.errors import DuplicateCalorieReferenceError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.calories import CalorieReference
from catalog.domain.ingredient import Ingredient
from shared.text import normalize_text
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class CalorieImportRun:
    updated: tuple[str, ...]
    unchanged: tuple[str, ...]
    skipped_manual: tuple[str, ...]
    unknown: tuple[str, ...]


class _RunLog:
    def __init__(self) -> None:
        self.updated: list[str] = []
        self.unchanged: list[str] = []
        self.skipped_manual: list[str] = []
        self.unknown: list[str] = []

    def freeze(self) -> CalorieImportRun:
        return CalorieImportRun(
            updated=tuple(self.updated),
            unchanged=tuple(self.unchanged),
            skipped_manual=tuple(self.skipped_manual),
            unknown=tuple(self.unknown),
        )


class ImportTagCalories:
    def __init__(self, ingredients: IngredientRepository, transactions: TransactionManager) -> None:
        self._ingredients = ingredients
        self._transactions = transactions

    def execute(self, references: tuple[CalorieReference, ...]) -> CalorieImportRun:
        normalized_names = [normalize_text(reference.tag_name) for reference in references]
        run = _RunLog()
        imported_ids: set[int] = set()
        with self._transactions.atomic():
            found = self._ingredients.find_by_normalized_names(set(normalized_names))
            for reference, normalized_name in zip(references, normalized_names, strict=True):
                ingredient = found.get(normalized_name)
                if ingredient is None:
                    run.unknown.append(reference.tag_name)
                    continue
                if ingredient.id in imported_ids:
                    raise DuplicateCalorieReferenceError(
                        f"{reference.tag_name!r} names the tag {ingredient.name!r} again."
                    )
                imported_ids.add(ingredient.id)
                self._apply(ingredient, reference, run)
        return run.freeze()

    def _apply(self, ingredient: Ingredient, reference: CalorieReference, run: _RunLog) -> None:
        current = ingredient.calories
        if current is not None and current.is_manual:
            run.skipped_manual.append(ingredient.name)
            return
        if current == reference.calories:
            run.unchanged.append(ingredient.name)
            return
        self._ingredients.save_calories(ingredient.id, reference.calories)
        run.updated.append(ingredient.name)
