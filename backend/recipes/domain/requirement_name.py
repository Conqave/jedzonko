from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecipeRequirementName:
    name: str
    normalized_name: str
