from datetime import datetime

from recipes.application.ports.ingredient_line_repository import IngredientLineRepository
from recipes.domain.external_line import LineInterpretation
from recipes.models import ExternalIngredientLine


class DjangoIngredientLineRepository(IngredientLineRepository):
    def find_interpretations(
        self, normalized_texts: tuple[str, ...]
    ) -> dict[str, LineInterpretation]:
        rows = ExternalIngredientLine.objects.filter(normalized_text__in=normalized_texts)
        return {row.normalized_text: _to_interpretation(row) for row in rows}

    def save_interpretations(
        self,
        interpretations: dict[str, LineInterpretation],
        model_name: str,
        interpreted_at: datetime,
    ) -> None:
        rows = [
            ExternalIngredientLine(
                normalized_text=text,
                ingredient_id=interpretation.ingredient_id,
                quantity=interpretation.quantity,
                unit_code=interpretation.unit_code,
                model_name=model_name,
                interpreted_at=interpreted_at,
            )
            for text, interpretation in interpretations.items()
        ]
        ExternalIngredientLine.objects.bulk_create(
            rows,
            update_conflicts=True,
            update_fields=["ingredient", "quantity", "unit_code", "model_name", "interpreted_at"],
        )


def _to_interpretation(row: ExternalIngredientLine) -> LineInterpretation:
    return LineInterpretation(
        ingredient_id=row.ingredient_id, quantity=row.quantity, unit_code=row.unit_code
    )
