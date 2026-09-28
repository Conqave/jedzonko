from datetime import datetime

from django.db.models import Count

from households.application.errors import HouseholdNotFoundError
from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.domain.deleted_household import DeletedHousehold
from households.domain.models import HouseholdSummary
from households.models import Household, HouseholdMembership


class DjangoHouseholdLifecycleRepository(HouseholdLifecycleRepository):
    def is_member_including_deleted(self, user_id: int, household_id: int) -> bool:
        return HouseholdMembership.objects.filter(
            user_id=user_id, household_id=household_id
        ).exists()

    def mark_deleted(self, household_id: int, deleted_at: datetime) -> None:
        updated = Household.objects.filter(pk=household_id, deleted_at__isnull=True).update(
            deleted_at=deleted_at
        )
        if updated == 0:
            raise HouseholdNotFoundError

    def find_deleted(self, household_id: int) -> DeletedHousehold | None:
        row = (
            Household.objects.filter(pk=household_id, deleted_at__isnull=False)
            .annotate(number_of_members=Count("memberships"))
            .first()
        )
        if row is None:
            return None
        return _to_deleted_household(row.pk, row.name, row.number_of_members, row.deleted_at)

    def find_deleted_for_user(self, user_id: int) -> list[DeletedHousehold]:
        rows = (
            Household.objects.filter(
                pk__in=HouseholdMembership.objects.filter(user_id=user_id).values("household_id"),
                deleted_at__isnull=False,
            )
            .annotate(number_of_members=Count("memberships"))
            .order_by("deleted_at", "name")
        )
        return [
            _to_deleted_household(row.pk, row.name, row.number_of_members, row.deleted_at)
            for row in rows
        ]

    def restore(self, household_id: int) -> HouseholdSummary:
        updated = Household.objects.filter(pk=household_id, deleted_at__isnull=False).update(
            deleted_at=None
        )
        if updated == 0:
            raise HouseholdNotFoundError
        row = (
            Household.objects.filter(pk=household_id)
            .annotate(number_of_members=Count("memberships"))
            .get()
        )
        return HouseholdSummary(id=row.pk, name=row.name, member_count=row.number_of_members)

    def find_deleted_before(self, cutoff: datetime) -> list[DeletedHousehold]:
        rows = (
            Household.objects.filter(deleted_at__isnull=False, deleted_at__lte=cutoff)
            .annotate(number_of_members=Count("memberships"))
            .order_by("deleted_at", "name")
        )
        return [
            _to_deleted_household(row.pk, row.name, row.number_of_members, row.deleted_at)
            for row in rows
        ]

    def purge(self, household_ids: list[int]) -> None:
        Household.objects.filter(pk__in=household_ids).delete()


def _to_deleted_household(
    household_id: int, name: str, member_count: int, deleted_at: datetime | None
) -> DeletedHousehold:
    if deleted_at is None:
        raise HouseholdNotFoundError
    return DeletedHousehold(
        id=household_id, name=name, member_count=member_count, deleted_at=deleted_at
    )
