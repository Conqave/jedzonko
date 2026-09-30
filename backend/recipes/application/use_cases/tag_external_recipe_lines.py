from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from recipes.application.ports.external_recipe_catalog import ExternalRecipeCatalog
from recipes.application.ports.ingredient_lines import IngredientLines


@dataclass(frozen=True, slots=True)
class ExternalLineTaggingRun:
    pending_count: int
    selected_count: int
    interpreted_count: int


class TagExternalRecipeLines:
    def __init__(self, catalog: ExternalRecipeCatalog, lines: IngredientLines) -> None:
        self._catalog = catalog
        self._lines = lines

    def execute(
        self,
        batch_size: int,
        limit: int | None,
        now: datetime,
        report: Callable[[int, int], None],
    ) -> ExternalLineTaggingRun:
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if limit is not None and limit < 1:
            raise ValueError("limit must be at least 1")
        texts = self._catalog.list_ingredient_texts()
        known = self._lines.find_interpretations(texts)
        pending = tuple(text for text in texts if text not in known)
        selected = pending if limit is None else pending[:limit]
        interpreted_count = 0
        for start in range(0, len(selected), batch_size):
            batch = selected[start : start + batch_size]
            interpreted_count += self._lines.interpret(batch, now)
            report(start + len(batch), len(selected))
        return ExternalLineTaggingRun(
            pending_count=len(pending),
            selected_count=len(selected),
            interpreted_count=interpreted_count,
        )
