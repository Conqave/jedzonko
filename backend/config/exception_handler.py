from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler

from accounts.presentation.errors import API_ERRORS as ACCOUNTS_API_ERRORS
from catalog.presentation.errors import API_ERRORS as CATALOG_API_ERRORS
from config.api_errors import ApiErrors
from config.shared_api_errors import API_ERRORS as SHARED_API_ERRORS
from households.presentation.errors import API_ERRORS as HOUSEHOLDS_API_ERRORS
from inventory.presentation.errors import API_ERRORS as INVENTORY_API_ERRORS
from promotions.presentation.errors import API_ERRORS as PROMOTIONS_API_ERRORS
from recipes.presentation.errors import API_ERRORS as RECIPES_API_ERRORS
from shopping.presentation.errors import API_ERRORS as SHOPPING_API_ERRORS

API_ERRORS: ApiErrors = {
    **SHARED_API_ERRORS,
    **ACCOUNTS_API_ERRORS,
    **CATALOG_API_ERRORS,
    **HOUSEHOLDS_API_ERRORS,
    **INVENTORY_API_ERRORS,
    **PROMOTIONS_API_ERRORS,
    **RECIPES_API_ERRORS,
    **SHOPPING_API_ERRORS,
}


def _to_api_exception(exc: Exception) -> Exception:
    for error_class in type(exc).__mro__:
        registered = API_ERRORS.get(error_class)
        if registered is not None:
            api_exception, detail, code = registered
            return api_exception(detail=detail, code=code)
    if isinstance(exc, Http404):
        return NotFound()
    if isinstance(exc, DjangoPermissionDenied):
        return PermissionDenied()
    return exc


def _resolve_code(exc: APIException) -> str:
    codes = exc.get_codes()
    if isinstance(codes, str):
        return codes
    if isinstance(codes, list) and len(codes) == 1 and isinstance(codes[0], str):
        return codes[0]
    return "invalid"


def handle_api_exception(exc: Exception, context: dict[str, object]) -> Response | None:
    translated = _to_api_exception(exc)
    if not isinstance(translated, APIException):
        return None
    response = exception_handler(translated, context)
    if response is None:
        raise AssertionError("DRF did not handle an APIException.")
    code = _resolve_code(translated)
    payload: dict[str, object] = {"code": code}
    if isinstance(response.data, dict) and "detail" in response.data:
        payload["detail"] = str(response.data["detail"])
    elif isinstance(response.data, list) and len(response.data) == 1:
        payload["detail"] = str(response.data[0])
    else:
        payload["detail"] = "Request failed."
        payload["errors"] = response.data
    response.data = payload
    return response
