from rest_framework import status
from rest_framework.exceptions import APIException


class RecipeSourceUnavailableError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "The external recipe source is unavailable."
    default_code = "recipe_source_unavailable"


class RecipeSourceContractInvalidError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "The external recipe source returned an unexpected payload."
    default_code = "recipe_source_contract_invalid"
