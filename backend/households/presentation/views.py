from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api import current_user_id
from config.composition import container
from households.presentation.serializers import (
    AddHouseholdMemberSerializer,
    CreateHouseholdSerializer,
    DeletedHouseholdSerializer,
    HouseholdMemberSerializer,
    HouseholdSerializer,
    RenameHouseholdSerializer,
)


class HouseholdListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        use_case = container().households.list_user_households
        households = use_case.execute(user_id)
        serializer = HouseholdSerializer(households, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        user_id = current_user_id(request)
        payload = CreateHouseholdSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().households.create_household
        household = use_case.execute(payload.validated_data["name"], user_id)
        serializer = HouseholdSerializer(household)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HouseholdDetailView(APIView):
    def patch(self, request: Request, household_id: int) -> Response:
        user_id = current_user_id(request)
        payload = RenameHouseholdSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().households.rename_household
        household = use_case.execute(user_id, household_id, payload.validated_data["name"])
        serializer = HouseholdSerializer(household)
        return Response(serializer.data)

    def delete(self, request: Request, household_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        use_case = container().households.delete_household
        use_case.execute(user_id, household_id, now)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeletedHouseholdListView(APIView):
    def get(self, request: Request) -> Response:
        user_id = current_user_id(request)
        use_case = container().households.list_deleted_households
        households = use_case.execute(user_id)
        serializer = DeletedHouseholdSerializer(households, many=True)
        return Response(serializer.data)


class HouseholdRestoreView(APIView):
    def post(self, request: Request, household_id: int) -> Response:
        user_id = current_user_id(request)
        now = timezone.now()
        use_case = container().households.restore_household
        household = use_case.execute(user_id, household_id, now)
        serializer = HouseholdSerializer(household)
        return Response(serializer.data)


class HouseholdMemberListView(APIView):
    def get(self, request: Request, household_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().households.list_household_members
        members = use_case.execute(user_id, household_id)
        serializer = HouseholdMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request: Request, household_id: int) -> Response:
        user_id = current_user_id(request)
        payload = AddHouseholdMemberSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        use_case = container().households.add_household_member
        member = use_case.execute(user_id, household_id, payload.validated_data["username"])
        serializer = HouseholdMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HouseholdMemberDetailView(APIView):
    def delete(self, request: Request, household_id: int, member_user_id: int) -> Response:
        user_id = current_user_id(request)
        use_case = container().households.remove_household_member
        use_case.execute(user_id, household_id, member_user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
