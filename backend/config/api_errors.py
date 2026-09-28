from collections.abc import Mapping

from rest_framework import status
from rest_framework.exceptions import APIException

ApiErrors = Mapping[type[Exception], tuple[type[APIException], str, str]]


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class BadGateway(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
