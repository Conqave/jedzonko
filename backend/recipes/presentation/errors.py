from rest_framework.exceptions import NotFound, ValidationError

from config.api_errors import ApiErrors, BadGateway, ServiceUnavailable
from recipes.application.errors import (
    DuplicateRecipeIngredientError,
    InvalidServingsError,
    MeasurementUnitNotFoundError,
    RecipeCategoryNotFoundError,
    RecipeNotFoundAtSourceError,
    RecipeNotFoundError,
    RecipeSourceContractError,
    RecipeSourceUnavailableError,
)

API_ERRORS: ApiErrors = {
    RecipeNotFoundError: (NotFound, "Recipe not found.", "recipe_not_found"),
    DuplicateRecipeIngredientError: (
        ValidationError,
        "The recipe lists the same ingredient twice.",
        "duplicate_recipe_ingredient",
    ),
    MeasurementUnitNotFoundError: (
        ValidationError,
        "Measurement unit not found.",
        "measurement_unit_not_found",
    ),
    RecipeCategoryNotFoundError: (
        ValidationError,
        "Recipe category not found.",
        "recipe_category_not_found",
    ),
    InvalidServingsError: (ValidationError, "Servings must be at least 1.", "invalid_servings"),
    RecipeNotFoundAtSourceError: (
        NotFound,
        "External recipe not found.",
        "external_recipe_not_found",
    ),
    RecipeSourceUnavailableError: (
        ServiceUnavailable,
        "The external recipe source is unavailable.",
        "recipe_source_unavailable",
    ),
    RecipeSourceContractError: (
        BadGateway,
        "The external recipe source returned an unexpected payload.",
        "recipe_source_contract_invalid",
    ),
}
