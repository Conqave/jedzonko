from dataclasses import dataclass
from decimal import Decimal

from recipes.domain.difficulty import RecipeDifficulty


@dataclass(frozen=True, slots=True)
class RecipeStepInput:
    position: int
    text: str


@dataclass(frozen=True, slots=True)
class RecipeIngredientInput:
    ingredient_id: int
    quantity: Decimal
    unit_code: str


@dataclass(frozen=True, slots=True)
class RecipeInput:
    name: str
    description: str
    servings: int
    preparation_time_minutes: int
    cooking_time_minutes: int
    difficulty: RecipeDifficulty
    category_id: int | None
    tag_names: tuple[str, ...]
    steps: tuple[RecipeStepInput, ...]
    ingredients: tuple[RecipeIngredientInput, ...]
