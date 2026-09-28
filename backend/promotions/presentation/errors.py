from rest_framework.exceptions import ValidationError

from config.api_errors import ApiErrors, BadGateway, ServiceUnavailable
from promotions.application.errors import (
    InvalidPromotionQueryError,
    InvalidShopSelectionError,
    PromotionSourceContractError,
    PromotionSourceUnavailableError,
)
from promotions.application.use_cases.set_favourite_shops import UnknownShopError

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
