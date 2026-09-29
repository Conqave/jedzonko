from datetime import datetime

from catalog.application.ports.ingredient_line_repository import IngredientLineRepository
from catalog.domain.ingredient_line import LineInterpretation
from catalog.models import IngredientLine


class DjangoIngredientLineRepository(IngredientLineRepository):
    def find_interpretations(
        self, normalized_texts: tuple[str, ...]
    ) -> dict[str, LineInterpretation]:
        rows = IngredientLine.objects.filter(normalized_text__in=normalized_texts)
        return {row.normalized_text: _to_interpretation(row) for row in rows}

    def save_interpretations(
        self,
        interpretations: dict[str, LineInterpretation],
        model_name: str,
        interpreted_at: datetime,
    ) -> None:
        rows = [
            IngredientLine(
                normalized_text=text,
                ingredient_id=interpretation.ingredient_id,
                quantity=interpretation.quantity,
                unit_code=interpretation.unit_code,
                model_name=model_name,
                interpreted_at=interpreted_at,
            )
            for text, interpretation in interpretations.items()
        ]
        IngredientLine.objects.bulk_create(
            rows,
            update_conflicts=True,
            update_fields=["ingredient", "quantity", "unit_code", "model_name", "interpreted_at"],
        )

    def reassign(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        IngredientLine.objects.filter(ingredient_id=source_ingredient_id).update(
            ingredient_id=target_ingredient_id
        )


def _to_interpretation(row: IngredientLine) -> LineInterpretation:
    return LineInterpretation(
        ingredient_id=row.ingredient_id, quantity=row.quantity, unit_code=row.unit_code
    )
