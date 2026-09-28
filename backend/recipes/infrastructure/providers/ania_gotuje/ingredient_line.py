import re
from decimal import Decimal

from recipes.domain.external import ExternalRecipeIngredient
from shared.measurement_units import find_measurement_unit

_SEPARATOR = re.compile(r"\s+[-\u2013]\s+")
_TRAILING_AMOUNT = re.compile(r"^(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>[a-ząćęłńóśźż]+)$")


def parse_ingredient_line(line: str) -> ExternalRecipeIngredient:
    source_text = " ".join(line.split())
    parts = _SEPARATOR.split(source_text)
    if len(parts) >= 2:
        tail = parts[-1]
        match = _TRAILING_AMOUNT.match(tail.casefold())
        if match is not None:
            unit_code = match.group("unit")
            unit = find_measurement_unit(unit_code)
            if unit is not None:
                amount_text = match.group("amount").replace(",", ".")
                amount = Decimal(amount_text)
                name = " - ".join(parts[:-1])
                return ExternalRecipeIngredient(
                    source_text=source_text,
                    name=name,
                    quantity=amount,
                    unit_code=unit.code,
                )
    return ExternalRecipeIngredient(
        source_text=source_text, name=source_text, quantity=None, unit_code=None
    )
