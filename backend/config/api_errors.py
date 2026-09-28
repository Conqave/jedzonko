from collections.abc import Mapping

from rest_framework.exceptions import APIException

ApiErrors = Mapping[type[Exception], tuple[type[APIException], str, str]]
