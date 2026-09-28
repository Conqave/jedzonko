from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.application.errors import (
    InvalidCredentialsError,
    NotAuthenticatedError,
    WrongCurrentPasswordError,
)
from config.api_errors import ApiErrors

API_ERRORS: ApiErrors = {
    InvalidCredentialsError: (
        PermissionDenied,
        "Invalid username or password.",
        "invalid_credentials",
    ),
    NotAuthenticatedError: (
        PermissionDenied,
        "Authentication credentials were not provided.",
        "not_authenticated",
    ),
    WrongCurrentPasswordError: (
        ValidationError,
        "The current password is wrong.",
        "wrong_current_password",
    ),
}
