import re
from decimal import Decimal

from recipes.domain.external import ExternalRecipeIngredient
from shared.measurement_units import find_measurement_unit

# The source states every ingredient as one free-text line. Only the trailing
# "- <number> <unit>" form carries an unambiguous amount; anything else (a hedge
# word, an extra remark, a household measure) stays text.
_SEPARATOR = re.compile(r"\s+[-\u2013]\s+")
_TRAILING_AMOUNT = re.compile(r"^(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>[a-ząćęłńóśźż]+)$")


def parse_ingredient_line(line: str) -> ExternalRecipeIngredient:
    source_text = " ".join(line.split())
    parts = _SEPARATOR.split(source_text)
    if len(parts) >= 2:
        tail = parts[-1]
        match = _TRAILING_AMOUNT.match(tail.casefold())
        if match is not None:
            unit = find_measurement_unit(match.group("unit"))
            if unit is not None:
                amount = Decimal(match.group("amount").replace(",", "."))
                return ExternalRecipeIngredient(
                    source_text=source_text,
                    name=" - ".join(parts[:-1]),
                    quantity=amount,
                    unit_code=unit.code,
                )
    return ExternalRecipeIngredient(
        source_text=source_text, name=source_text, quantity=None, unit_code=None
    )
