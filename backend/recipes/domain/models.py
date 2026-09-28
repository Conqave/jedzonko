from dataclasses import dataclass
from decimal import Decimal

from recipes.domain.difficulty import RecipeDifficulty
from shared.measurement import Quantity


@dataclass(frozen=True, slots=True)
class RecipeRequirement:
    name: str
    ingredient_id: int | None
    quantity: Quantity | None


@dataclass(frozen=True, slots=True)
class RecipeStepDetail:
    position: int
    text: str


@dataclass(frozen=True, slots=True)
class RecipeIngredientDetail:
    name: str
    ingredient_id: int | None
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
    author_username: str


@dataclass(frozen=True, slots=True)
class RecipeDetail:
    summary: RecipeSummary
    steps: tuple[RecipeStepDetail, ...]
    ingredients: tuple[RecipeIngredientDetail, ...]
