from dataclasses import dataclass
from decimal import Decimal

from catalog.domain.measurement import Quantity
from recipes.domain.difficulty import RecipeDifficulty


@dataclass(frozen=True, slots=True)
class RecipeRequirement:
    ingredient_id: int
    ingredient_name: str
    quantity: Quantity


@dataclass(frozen=True, slots=True)
class RecipeStepDetail:
    position: int
    text: str


@dataclass(frozen=True, slots=True)
class RecipeIngredientDetail:
    ingredient_id: int
    ingredient_name: str
    quantity: Decimal
    unit_code: str


@dataclass(frozen=True, slots=True)
class RecipeSummary:
    id: int
    name: str
    description: str
    servings: int
    preparation_time_minutes: int
    cooking_time_minutes: int
    difficulty: RecipeDifficulty
    category_name: str | None
    tag_names: tuple[str, ...]
    image_url: str | None


@dataclass(frozen=True, slots=True)
class RecipeDetail:
    summary: RecipeSummary
    steps: tuple[RecipeStepDetail, ...]
    ingredients: tuple[RecipeIngredientDetail, ...]
