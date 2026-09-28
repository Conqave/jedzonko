from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from config.api_errors import ApiErrors, ServiceUnavailable
from shopping.application.errors import (
    ExternalRecipeNotFoundError,
    IngredientNotFoundError,
    InvalidShoppingItemError,
    NoShopsChosenError,
    NothingToSplitError,
    PrimaryShoppingListCannotBeDeletedError,
    PrimaryShoppingListNotFoundError,
    ProductNotFoundError,
    PromotionsNotAllowedError,
    PromotionsUnavailableError,
    RecipesUnavailableError,
    ShoppingItemAlreadyPendingError,
    ShoppingItemMergeConflictError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.domain.errors import InvalidShoppingSubjectError

API_ERRORS: ApiErrors = {
    ExternalRecipeNotFoundError: (
        NotFound,
        "External recipe not found.",
        "external_recipe_not_found",
    ),
    RecipesUnavailableError: (
        ServiceUnavailable,
        "The external recipe source is unavailable.",
        "recipe_source_unavailable",
    ),
    NoShopsChosenError: (ValidationError, "Choose at least one shop.", "no_shops_chosen"),
    NothingToSplitError: (
        ValidationError,
        "The list has no items left to buy.",
        "nothing_to_split",
    ),
    PromotionsNotAllowedError: (
        PermissionDenied,
        "You do not have access to promotions.",
        "promotions_not_allowed",
    ),
    PromotionsUnavailableError: (
        ServiceUnavailable,
        "The promotion provider is currently unavailable.",
        "promotion_source_unavailable",
    ),
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
