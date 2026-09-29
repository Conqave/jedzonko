from catalog.domain.ingredient import Ingredient
from shared.measurement_units import MEASUREMENT_UNIT_CODES

_INSTRUCTIONS = (
    "Linie składników pochodzą z polskiego przepisu kulinarnego. Dla każdej linii:\n"
    "- wybierz numer składnika z listy, który ta linia oznacza; przy „A lub B” wybierz "
    "pierwszy pasujący; jeśli żaden nie pasuje, wybierz 0;\n"
    "- podaj ilość i jednostkę tylko wtedy, gdy linia podaje je wprost w jednej z jednostek: "
    "{units}; sztuki to „szt”; miar kuchennych jak szklanka, łyżka czy szczypta nie "
    "przeliczaj; w każdym innym wypadku ilość i jednostka to null."
)


def build_line_prompt(lines: tuple[str, ...], tags: tuple[Ingredient, ...]) -> str:
    units = ", ".join(MEASUREMENT_UNIT_CODES)
    instructions = _INSTRUCTIONS.format(units=units)
    choice_listing = "\n".join(
        f"{position}. {choice.name}" for position, choice in enumerate(tags, start=1)
    )
    line_listing = "\n".join(f"{position}. {line}" for position, line in enumerate(lines, start=1))
    return (
        f"{instructions}\n\n"
        f"Składniki:\n{choice_listing}\n\n"
        f"Linie:\n{line_listing}\n\n"
        "Odpowiedz obiektem JSON z listą „lines”, po jednym wpisie na każdą linię."
    )


def build_line_schema() -> dict[str, object]:
    unit_codes: list[object] = [*MEASUREMENT_UNIT_CODES, None]
    entry = {
        "type": "object",
        "properties": {
            "line": {"type": "integer"},
            "ingredient": {"type": "integer"},
            "quantity": {"type": ["string", "null"]},
            "unit": {"type": ["string", "null"], "enum": unit_codes},
        },
        "required": ["line", "ingredient", "quantity", "unit"],
    }
    return {
        "type": "object",
        "properties": {"lines": {"type": "array", "items": entry}},
        "required": ["lines"],
    }
