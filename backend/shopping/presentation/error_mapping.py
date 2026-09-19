from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied

from households.application.errors import NotAHouseholdMemberError
from shopping.application.errors import (
    InvalidShoppingItemError,
    ProductNotFoundError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)


class ShoppingBadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


_ERROR_RESPONSES: dict[type[Exception], tuple[type[APIException], str, str]] = {
    NotAHouseholdMemberError: (
        PermissionDenied,
        "Not a household member.",
        "not_a_household_member",
    ),
    ShoppingListNotFoundError: (NotFound, "Shopping list not found.", "shopping_list_not_found"),
    ShoppingListItemNotFoundError: (
        NotFound,
        "Shopping item not found.",
        "shopping_item_not_found",
    ),
    InvalidShoppingItemError: (
        ShoppingBadRequest,
        "Invalid shopping item.",
        "invalid_shopping_item",
    ),
    ProductNotFoundError: (ShoppingBadRequest, "Unknown product.", "product_not_found"),
}

HANDLED_ERRORS = tuple(_ERROR_RESPONSES)


def to_api_exception(error: Exception) -> APIException:
    exception_class, detail, code = _ERROR_RESPONSES[type(error)]
    return exception_class(detail=detail, code=code)
