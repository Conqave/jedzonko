from dataclasses import dataclass, replace
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ExternalRecipeIngredient:
    source_text: str
    name: str
    quantity: Decimal | None
    unit_code: str | None


@dataclass(frozen=True, slots=True)
class ExternalRecipeContent:
    yield_label: str | None
    ingredients: tuple[ExternalRecipeIngredient, ...]


@dataclass(frozen=True, slots=True)
class ExternalRecipeSummary:
    source_name: str
    source_url: str
    reference: str
    name: str
    description: str
    image_url: str | None
    yield_label: str
    total_time_minutes: int | None
    tag_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalRecipeDetail:
    summary: ExternalRecipeSummary
    preparation_time_minutes: int | None
    cooking_time_minutes: int | None
    steps: tuple[str, ...]
    ingredients: tuple[ExternalRecipeIngredient, ...]


@dataclass(frozen=True, slots=True)
class ExternalRecipePage:
    recipes: tuple[ExternalRecipeSummary, ...]
    page: int
    page_size: int
    total_count: int
    total_pages: int


@dataclass(frozen=True, slots=True)
class ExternalRecipeMatch:
    summary: ExternalRecipeSummary
    matched_product_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MatchedExternalRecipePage:
    matches: tuple[ExternalRecipeMatch, ...]
    page: int
    page_size: int
    total_count: int
    total_pages: int


@dataclass(frozen=True, slots=True)
class ImportedExternalRecipe:
    reference: str
    name: str
    source_url: str
    image_source_url: str | None
    yield_label: str | None
    ingredients: tuple[ExternalRecipeIngredient, ...]


@dataclass(frozen=True, slots=True)
class RecipeImage:
    filename: str
    content: bytes


def with_local_image(
    summary: ExternalRecipeSummary, local_image_urls: dict[str, str]
) -> ExternalRecipeSummary:
    local_url = local_image_urls.get(summary.reference)
    if local_url is None:
        return summary
    return replace(summary, image_url=local_url)


def with_local_images(
    page: ExternalRecipePage, local_image_urls: dict[str, str]
) -> ExternalRecipePage:
    recipes = tuple(with_local_image(summary, local_image_urls) for summary in page.recipes)
    return replace(page, recipes=recipes)
