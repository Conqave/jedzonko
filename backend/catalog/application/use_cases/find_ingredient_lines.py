from catalog.application.ports.ingredient_line_repository import IngredientLineRepository
from catalog.domain.ingredient_line import LineInterpretation
from shared.text import normalize_text


class FindIngredientLines:
    def __init__(self, lines: IngredientLineRepository) -> None:
        self._lines = lines

    def execute(self, texts: tuple[str, ...]) -> dict[str, LineInterpretation]:
        normalized = {text: normalize_text(text) for text in texts}
        known = self._lines.find_interpretations(tuple(value for value in normalized.values()))
        return {text: known[key] for text, key in normalized.items() if key in known}
