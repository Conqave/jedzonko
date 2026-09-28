from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IngredientRequirement:
    name: str
    normalized_name: str
