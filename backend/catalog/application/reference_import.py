from dataclasses import dataclass
from enum import StrEnum

from catalog.application.errors import DuplicateTagReferenceError
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.ingredient import Ingredient
from catalog.domain.provenance import ReferenceImportDecision
from shared.text import normalize_text


class TagFact(StrEnum):
    CALORIES = "kcal_per_100g"
    PIECE_WEIGHT = "grams_per_piece"
    DENSITY = "grams_per_ml"


@dataclass(frozen=True, slots=True)
class ImportedFact:
    tag_name: str
    fact: TagFact


@dataclass(frozen=True, slots=True)
class ReferenceImportRun:
    updated: tuple[ImportedFact, ...]
    unchanged: tuple[ImportedFact, ...]
    skipped_manual: tuple[ImportedFact, ...]
    unknown: tuple[str, ...]


class ReferenceImportLog:
    def __init__(self) -> None:
        self._updated: list[ImportedFact] = []
        self._unchanged: list[ImportedFact] = []
        self._skipped_manual: list[ImportedFact] = []
        self._unknown: list[str] = []

    def record(self, tag: Ingredient, fact: TagFact, decision: ReferenceImportDecision) -> None:
        entry = ImportedFact(tag_name=tag.name, fact=fact)
        match decision:
            case ReferenceImportDecision.UPDATE:
                self._updated.append(entry)
            case ReferenceImportDecision.UNCHANGED:
                self._unchanged.append(entry)
            case ReferenceImportDecision.KEEP_MANUAL:
                self._skipped_manual.append(entry)

    def record_unknown(self, tag_name: str) -> None:
        self._unknown.append(tag_name)

    def freeze(self) -> ReferenceImportRun:
        return ReferenceImportRun(
            updated=tuple(self._updated),
            unchanged=tuple(self._unchanged),
            skipped_manual=tuple(self._skipped_manual),
            unknown=tuple(self._unknown),
        )


def find_referenced_tags(
    ingredients: IngredientRepository, tag_names: tuple[str, ...]
) -> tuple[Ingredient | None, ...]:
    normalized_names = [normalize_text(tag_name) for tag_name in tag_names]
    found = ingredients.find_by_normalized_names(set(normalized_names))
    tags: list[Ingredient | None] = []
    referenced_ids: set[int] = set()
    for tag_name, normalized_name in zip(tag_names, normalized_names, strict=True):
        tag = found.get(normalized_name)
        if tag is not None and tag.id in referenced_ids:
            raise DuplicateTagReferenceError(f"{tag_name!r} names the tag {tag.name!r} again.")
        if tag is not None:
            referenced_ids.add(tag.id)
        tags.append(tag)
    return tuple(tags)
