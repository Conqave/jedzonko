from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from config.api_errors import ApiErrors
from promotions.application.errors import InvalidPromotionQueryError, InvalidShopSelectionError
from promotions.application.ports.promotion_source import (
    PromotionSourceContractError,
    PromotionSourceUnavailableError,
)
from promotions.application.use_cases.set_favourite_shops import UnknownShopError


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class BadGateway(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY


API_ERRORS: ApiErrors = {
    PromotionSourceUnavailableError: (
        ServiceUnavailable,
        "The promotion provider is currently unavailable.",
        "promotion_source_unavailable",
    ),
    PromotionSourceContractError: (
        BadGateway,
        "The promotion provider returned an unexpected response.",
        "promotion_source_contract_invalid",
    ),
    UnknownShopError: (ValidationError, "Unknown shop.", "unknown_shop"),
    InvalidPromotionQueryError: (ValidationError, "The query is empty.", "invalid_query"),
    InvalidShopSelectionError: (ValidationError, "A shop slug is empty.", "invalid_query"),
}
