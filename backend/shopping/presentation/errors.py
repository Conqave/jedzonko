from rest_framework.exceptions import NotFound, ValidationError

from config.api_errors import ApiErrors
from shopping.application.errors import (
    IngredientNotFoundError,
    InvalidShoppingItemError,
    PrimaryShoppingListCannotBeDeletedError,
    PrimaryShoppingListNotFoundError,
    ProductNotFoundError,
    ShoppingItemAlreadyPendingError,
    ShoppingItemMergeConflictError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.domain.errors import InvalidShoppingSubjectError

API_ERRORS: ApiErrors = {
    ShoppingListNotFoundError: (NotFound, "Shopping list not found.", "shopping_list_not_found"),
    PrimaryShoppingListNotFoundError: (
        NotFound,
        "The household has no primary shopping list.",
        "primary_shopping_list_not_found",
    ),
    PrimaryShoppingListCannotBeDeletedError: (
        ValidationError,
        "The primary shopping list cannot be deleted.",
        "primary_shopping_list_cannot_be_deleted",
    ),
    ShoppingListItemNotFoundError: (
        NotFound,
        "Shopping item not found.",
        "shopping_item_not_found",
    ),
    InvalidShoppingItemError: (ValidationError, "Invalid shopping item.", "invalid_shopping_item"),
    InvalidShoppingSubjectError: (
        ValidationError,
        "A shopping item is about exactly one product, ingredient or text.",
        "invalid_shopping_item",
    ),
    ProductNotFoundError: (ValidationError, "Unknown product.", "product_not_found"),
    IngredientNotFoundError: (ValidationError, "Unknown ingredient.", "ingredient_not_found"),
    ShoppingItemAlreadyPendingError: (
        ValidationError,
        "The item is already on the list.",
        "shopping_item_already_pending",
    ),
    ShoppingItemMergeConflictError: (
        ValidationError,
        "The items use different units and cannot be merged.",
        "shopping_item_merge_conflict",
    ),
}
