from rest_framework.exceptions import PermissionDenied

from config.api_errors import ApiErrors
from shared.household_membership import NotAHouseholdMemberError

API_ERRORS: ApiErrors = {
    NotAHouseholdMemberError: (
        PermissionDenied,
        "Not a household member.",
        "not_a_household_member",
    ),
}
