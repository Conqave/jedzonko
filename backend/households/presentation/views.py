from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from households.application.errors import (
    LastMemberCannotLeaveError,
    MemberNotFoundError,
    NotAHouseholdMemberError,
)
from households.application.use_cases.add_household_member import AddHouseholdMember
from households.application.use_cases.create_household import CreateHousehold
from households.application.use_cases.list_household_members import ListHouseholdMembers
from households.application.use_cases.list_user_households import ListUserHouseholds
from households.application.use_cases.remove_household_member import RemoveHouseholdMember
from households.composition import build_household_access_policy, build_household_repository
from households.domain.models import HouseholdMember, HouseholdSummary
from households.presentation.serializers import (
    AddHouseholdMemberSerializer,
    CreateHouseholdSerializer,
)


def _current_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return user_id


def _represent_household(household: HouseholdSummary) -> dict[str, object]:
    return {"id": household.id, "name": household.name, "member_count": household.member_count}


def _represent_member(member: HouseholdMember) -> dict[str, object]:
    return {"user_id": member.user_id, "username": member.username}


class HouseholdListView(APIView):
    def get(self, request: Request) -> Response:
        use_case = ListUserHouseholds(build_household_repository())
        households = use_case.execute(_current_user_id(request))
        return Response([_represent_household(item) for item in households])

    def post(self, request: Request) -> Response:
        serializer = CreateHouseholdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        use_case = CreateHousehold(build_household_repository())
        household = use_case.execute(serializer.validated_data["name"], _current_user_id(request))
        return Response(_represent_household(household), status=status.HTTP_201_CREATED)


class HouseholdMemberListView(APIView):
    def get(self, request: Request, household_id: int) -> Response:
        use_case = ListHouseholdMembers(
            build_household_repository(), build_household_access_policy()
        )
        try:
            members = use_case.execute(_current_user_id(request), household_id)
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        return Response([_represent_member(member) for member in members])

    def post(self, request: Request, household_id: int) -> Response:
        serializer = AddHouseholdMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        use_case = AddHouseholdMember(build_household_repository(), build_household_access_policy())
        try:
            member = use_case.execute(
                _current_user_id(request), household_id, serializer.validated_data["username"]
            )
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except MemberNotFoundError:
            raise NotFound(detail="User not found.", code="user_not_found")
        return Response(_represent_member(member), status=status.HTTP_201_CREATED)


class HouseholdMemberDetailView(APIView):
    def delete(self, request: Request, household_id: int, member_user_id: int) -> Response:
        use_case = RemoveHouseholdMember(
            build_household_repository(), build_household_access_policy()
        )
        try:
            use_case.execute(_current_user_id(request), household_id, member_user_id)
        except NotAHouseholdMemberError:
            raise PermissionDenied(detail="Not a household member.", code="not_a_household_member")
        except MemberNotFoundError:
            raise NotFound(detail="Member not found.", code="member_not_found")
        except LastMemberCannotLeaveError:
            raise ValidationError(
                detail="The last member cannot be removed.", code="last_member_cannot_leave"
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
