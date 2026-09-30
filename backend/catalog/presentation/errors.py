from rest_framework.exceptions import NotFound, ValidationError

from catalog.application.errors import (
    DuplicateIngredientNameError,
    DuplicateProductError,
    IngredientClassifierContractError,
    IngredientClassifierUnavailableError,
    IngredientNotFoundError,
    ProductNotFoundError,
)
from catalog.domain.calories import MAX_KCAL_PER_100G
from catalog.domain.errors import (
    InvalidNameError,
    InvalidProductIngredientTransitionError,
    InvalidProductPackageError,
    InvalidTagCaloriesError,
    ProductIngredientNotFoundError,
    UnknownMeasurementUnitError,
)
from config.api_errors import ApiErrors, BadGateway, ServiceUnavailable

API_ERRORS: ApiErrors = {
    IngredientClassifierUnavailableError: (
        ServiceUnavailable,
        "The ingredient classification model is unavailable.",
        "ingredient_classifier_unavailable",
    ),
    IngredientClassifierContractError: (
        BadGateway,
        "The ingredient classification model gave an unusable answer.",
        "ingredient_classifier_contract_invalid",
    ),
    ProductNotFoundError: (NotFound, "Product not found.", "product_not_found"),
    DuplicateProductError: (
        ValidationError,
        "This product already exists in the household.",
        "duplicate_product",
    ),
    IngredientNotFoundError: (NotFound, "Ingredient not found.", "ingredient_not_found"),
    DuplicateIngredientNameError: (
        ValidationError,
        "This name already belongs to an ingredient.",
        "duplicate_ingredient_name",
    ),
    InvalidNameError: (ValidationError, "The name is empty or too long.", "invalid_name"),
    UnknownMeasurementUnitError: (
        ValidationError,
        "Unknown measurement unit.",
        "measurement_unit_not_found",
    ),
    InvalidProductPackageError: (
        ValidationError,
        "A package holds a positive quantity.",
        "invalid_package",
    ),
    InvalidTagCaloriesError: (
        ValidationError,
        f"Calories per 100 g lie between 0 and {MAX_KCAL_PER_100G} with one decimal place.",
        "invalid_tag_calories",
    ),
    ProductIngredientNotFoundError: (
        NotFound,
        "The product has no such ingredient decision.",
        "product_ingredient_not_found",
    ),
    InvalidProductIngredientTransitionError: (
        ValidationError,
        "The ingredient is already rejected.",
        "invalid_product_ingredient_transition",
    ),
}
