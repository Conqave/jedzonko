from dataclasses import dataclass
from datetime import datetime

from catalog.application.ports.ingredient_line_interpreter import IngredientLineInterpreter
from catalog.application.ports.ingredient_line_repository import IngredientLineRepository
from catalog.application.use_cases.list_tags import ListTags
from catalog.domain.ingredient_line import MAX_LINE_TEXT_LENGTH, LineInterpretation
from shared.text import normalize_text


@dataclass(frozen=True, slots=True)
class LineInterpretationRun:
    interpretations: dict[str, LineInterpretation]
    interpreted_count: int


class InterpretIngredientLines:
    def __init__(
        self,
        lines: IngredientLineRepository,
        interpreter: IngredientLineInterpreter,
        list_tags: ListTags,
    ) -> None:
        self._lines = lines
        self._interpreter = interpreter
        self._list_tags = list_tags

    def execute(self, texts: tuple[str, ...], now: datetime) -> LineInterpretationRun:
        normalized = {text: normalize_text(text) for text in texts}
        known = self._lines.find_interpretations(tuple(value for value in normalized.values()))
        unknown = {
            key: text
            for text, key in normalized.items()
            if key not in known and 0 < len(key) <= MAX_LINE_TEXT_LENGTH
        }
        tags = self._list_tags.execute()
        interpreted: dict[str, LineInterpretation] = {}
        if unknown and tags:
            unknown_lines = tuple(text for text in unknown.values())
            answers = self._interpreter.interpret(unknown_lines, tags)
            pairs = zip(unknown, answers, strict=True)
            interpreted = dict(pairs)
            self._lines.save_interpretations(interpreted, self._interpreter.model_name, now)
        stored = {**known, **interpreted}
        by_text = {text: stored[key] for text, key in normalized.items() if key in stored}
        return LineInterpretationRun(interpretations=by_text, interpreted_count=len(interpreted))
