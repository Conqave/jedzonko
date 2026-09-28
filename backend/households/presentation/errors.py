from rest_framework.exceptions import NotFound, ValidationError

from config.api_errors import ApiErrors
from households.application.errors import (
    HouseholdNotFoundError,
    LastMemberCannotLeaveError,
    MemberNotFoundError,
    RecoveryWindowExpiredError,
    UserNotFoundError,
)

API_ERRORS: ApiErrors = {
    HouseholdNotFoundError: (NotFound, "Household not found.", "household_not_found"),
    UserNotFoundError: (NotFound, "User not found.", "user_not_found"),
    MemberNotFoundError: (NotFound, "Member not found.", "member_not_found"),
    LastMemberCannotLeaveError: (
        ValidationError,
        "The last member cannot be removed.",
        "last_member_cannot_leave",
    ),
    RecoveryWindowExpiredError: (
        ValidationError,
        "The recovery window has expired.",
        "recovery_window_expired",
    ),
}
