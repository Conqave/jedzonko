from datetime import UTC, datetime
from decimal import Decimal

from catalog.application.ports.ingredient_line_interpreter import IngredientLineInterpreter
from catalog.application.use_cases.find_ingredient_lines import FindIngredientLines
from catalog.application.use_cases.interpret_ingredient_lines import InterpretIngredientLines
from catalog.application.use_cases.list_tags import ListTags
from catalog.domain.ingredient import Ingredient, IngredientNameSource
from catalog.domain.ingredient_line import LineInterpretation
from catalog.domain.names import CatalogName
from catalog.tests.fakes import FakeIngredientLineRepository, FakeIngredientRepository

NOW = datetime(2026, 9, 29, 8, 0, tzinfo=UTC)


class ScriptedInterpreter(IngredientLineInterpreter):
    def __init__(self, answers: dict[str, str | None]) -> None:
        self._answers = answers
        self.calls: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    @property
    def model_name(self) -> str:
        return "fake-model"

    def interpret(
        self, lines: tuple[str, ...], tags: tuple[Ingredient, ...]
    ) -> tuple[LineInterpretation, ...]:
        self.calls.append((lines, tuple(tag.name for tag in tags)))
        by_name = {tag.name: tag.id for tag in tags}
        return tuple(
            LineInterpretation(
                ingredient_id=(
                    None if self._answers[line] is None else by_name[self._answers[line] or ""]
                ),
                quantity=Decimal("3") if line.startswith("3") else None,
                unit_code="szt" if line.startswith("3") else None,
            )
            for line in lines
        )


class Setup:
    def __init__(self) -> None:
        self.ingredients = FakeIngredientRepository()
        for name in ["jajka", "mleko"]:
            self.ingredients.create(CatalogName.parse(name), IngredientNameSource.ANIA_GOTUJE)
        self.lines = FakeIngredientLineRepository({})

    def interpret(self, interpreter: ScriptedInterpreter, texts: tuple[str, ...]) -> int:
        use_case = InterpretIngredientLines(self.lines, interpreter, ListTags(self.ingredients))
        return use_case.execute(texts, NOW).interpreted_count


def test_unseen_lines_are_interpreted_against_every_tag_and_cached() -> None:
    setup = Setup()
    interpreter = ScriptedInterpreter({"3 średnie jajka": "jajka", "szczypta soli": None})

    count = setup.interpret(interpreter, ("3 średnie jajka", "szczypta soli"))

    assert count == 2
    assert interpreter.calls == [(("3 średnie jajka", "szczypta soli"), ("jajka", "mleko"))]
    found = FindIngredientLines(setup.lines).execute(("3 Średnie  jajka",))
    assert found["3 Średnie  jajka"].unit_code == "szt"


def test_cached_lines_are_not_sent_to_the_model_again() -> None:
    setup = Setup()
    setup.interpret(ScriptedInterpreter({"szklanka mleka": "mleko"}), ("szklanka mleka",))
    interpreter = ScriptedInterpreter({"3 jajka": "jajka"})

    count = setup.interpret(interpreter, ("szklanka mleka", "3 jajka"))

    assert count == 1
    assert [call[0] for call in interpreter.calls] == [("3 jajka",)]
