from rest_framework.exceptions import NotFound, ValidationError

from catalog.application.errors import (
    DuplicateIngredientNameError,
    DuplicateProductError,
    IngredientNotFoundError,
    ProductNotFoundError,
)
from catalog.domain.errors import (
    InvalidNameError,
    InvalidProductIngredientTransitionError,
    InvalidProductPackageError,
    ProductIngredientNotFoundError,
    UnknownMeasurementUnitError,
)
from config.api_errors import ApiErrors

API_ERRORS: ApiErrors = {
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
