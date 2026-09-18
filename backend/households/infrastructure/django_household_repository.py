from django.contrib.auth.models import User
from django.db.models import Count

from households.application.errors import HouseholdNotFoundError, MemberNotFoundError
from households.application.ports.household_repository import HouseholdRepository
from households.domain.models import HouseholdMember, HouseholdSummary
from households.models import Household, HouseholdMembership


class DjangoHouseholdRepository(HouseholdRepository):
    def find_households_for_user(self, user_id: int) -> list[HouseholdSummary]:
        rows = (
            Household.objects.filter(memberships__user_id=user_id, deleted_at__isnull=True)
            .annotate(number_of_members=Count("memberships"))
            .order_by("name")
        )
        return [
            HouseholdSummary(id=row.pk, name=row.name, member_count=row.number_of_members)
            for row in rows
        ]

    def find_household(self, household_id: int) -> HouseholdSummary | None:
        row = (
            Household.objects.filter(pk=household_id, deleted_at__isnull=True)
            .annotate(number_of_members=Count("memberships"))
            .first()
        )
        if row is None:
            return None
        return HouseholdSummary(id=row.pk, name=row.name, member_count=row.number_of_members)

    def is_member(self, user_id: int, household_id: int) -> bool:
        return HouseholdMembership.objects.filter(
            user_id=user_id, household_id=household_id, household__deleted_at__isnull=True
        ).exists()

    def list_members(self, household_id: int) -> list[HouseholdMember]:
        rows = HouseholdMembership.objects.filter(household_id=household_id).select_related("user")
        return [
            HouseholdMember(user_id=row.user_id, username=row.user.get_username()) for row in rows
        ]

    def create_household(self, name: str, owner_user_id: int) -> HouseholdSummary:
        household = Household.objects.create(name=name)
        HouseholdMembership.objects.create(household=household, user_id=owner_user_id)
        return HouseholdSummary(id=household.pk, name=household.name, member_count=1)

    def add_member(self, household_id: int, username: str) -> HouseholdMember:
        if not Household.objects.filter(pk=household_id, deleted_at__isnull=True).exists():
            raise HouseholdNotFoundError
        user = User.objects.filter(username=username).first()
        if user is None:
            raise MemberNotFoundError
        HouseholdMembership.objects.get_or_create(household_id=household_id, user=user)
        return HouseholdMember(user_id=user.pk, username=user.get_username())

    def remove_member(self, household_id: int, user_id: int) -> None:
        deleted, _ = HouseholdMembership.objects.filter(
            household_id=household_id, user_id=user_id
        ).delete()
        if deleted == 0:
            raise MemberNotFoundError

    def count_members(self, household_id: int) -> int:
        return HouseholdMembership.objects.filter(household_id=household_id).count()
