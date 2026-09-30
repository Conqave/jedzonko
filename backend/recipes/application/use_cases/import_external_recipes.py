from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from recipes.application.errors import (
    RecipeNotFoundAtSourceError,
    RecipeSourceContractError,
    RecipeSourceError,
)
from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.recipe_site import RecipeSite
from recipes.domain.external import ImportedExternalRecipe, RecipeImage
from shared.transactions import TransactionManager


class ImportOutcome(StrEnum):
    IMPORTED = "imported"
    IMPORTED_WITHOUT_IMAGE = "no-image"
    IMAGE_ADDED = "image"
    IMAGE_FAILED = "image-failed"
    MISSING = "missing"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class RecipeImportRun:
    listed_count: int
    skipped_count: int
    outcomes: dict[str, ImportOutcome]

    def count(self, outcome: ImportOutcome) -> int:
        return len([found for found in self.outcomes.values() if found is outcome])


class ImportExternalRecipes:
    def __init__(
        self,
        site: RecipeSite,
        catalog: ExternalRecipeCatalog,
        transactions: TransactionManager,
    ) -> None:
        self._site = site
        self._catalog = catalog
        self._transactions = transactions

    def execute(
        self,
        limit: int | None,
        refresh: bool,
        now: datetime,
        report: Callable[[str, ImportOutcome], None],
    ) -> RecipeImportRun:
        if limit is not None and limit < 1:
            raise ValueError("limit must be at least 1")
        references = self._site.list_recipe_references()
        stored = self._catalog.list_references()
        missing_images = {} if refresh else self._catalog.list_missing_images()
        pending = tuple(
            reference
            for reference in references
            if refresh or reference not in stored or reference in missing_images
        )
        selected = pending if limit is None else pending[:limit]
        outcomes: dict[str, ImportOutcome] = {}
        for reference in selected:
            image_url = missing_images.get(reference)
            if image_url is None:
                outcome = self._import(reference, now)
            else:
                outcome = self._add_image(reference, image_url)
            report(reference, outcome)
            outcomes[reference] = outcome
        return RecipeImportRun(
            listed_count=len(references),
            skipped_count=len(references) - len(pending),
            outcomes=outcomes,
        )

    def _import(self, reference: str, now: datetime) -> ImportOutcome:
        try:
            recipe = self._site.fetch_recipe(reference)
        except RecipeNotFoundAtSourceError:
            return ImportOutcome.MISSING
        except RecipeSourceContractError:
            return ImportOutcome.REJECTED
        image = self._fetch_image(recipe)
        with self._transactions.atomic():
            self._catalog.save_recipe(recipe, image, now)
        if recipe.image_source_url is not None and image is None:
            return ImportOutcome.IMPORTED_WITHOUT_IMAGE
        return ImportOutcome.IMPORTED

    def _add_image(self, reference: str, image_url: str) -> ImportOutcome:
        try:
            image = self._site.fetch_image(reference, image_url)
        except RecipeSourceError:
            return ImportOutcome.IMAGE_FAILED
        with self._transactions.atomic():
            self._catalog.save_image(reference, image)
        return ImportOutcome.IMAGE_ADDED

    def _fetch_image(self, recipe: ImportedExternalRecipe) -> RecipeImage | None:
        if recipe.image_source_url is None:
            return None
        try:
            return self._site.fetch_image(recipe.reference, recipe.image_source_url)
        except RecipeSourceError:
            return None
