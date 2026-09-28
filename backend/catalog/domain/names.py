from dataclasses import dataclass

from catalog.domain.errors import InvalidIngredientNameError
from shared.text import normalize_text

MAX_INGREDIENT_NAME_LENGTH = 120


@dataclass(frozen=True, slots=True)
class IngredientNameText:
    name: str
    normalized_name: str

    @classmethod
    def parse(cls, raw_name: str) -> "IngredientNameText":
        name = " ".join(raw_name.split())
        normalized_name = normalize_text(name)
        if not normalized_name:
            raise InvalidIngredientNameError("Ingredient name is empty.")
        if max(len(name), len(normalized_name)) > MAX_INGREDIENT_NAME_LENGTH:
            raise InvalidIngredientNameError(
                f"Ingredient name is longer than {MAX_INGREDIENT_NAME_LENGTH} characters."
            )
        return cls(name=name, normalized_name=normalized_name)
