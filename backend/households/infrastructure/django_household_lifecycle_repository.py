from datetime import datetime

from django.db.models import Count, QuerySet

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
        households = Household.objects.filter(pk=household_id, deleted_at__isnull=False)
        found = _to_deleted_households(households)
        return found[0] if found else None

    def find_deleted_for_user(self, user_id: int) -> list[DeletedHousehold]:
        households = Household.objects.filter(
            pk__in=HouseholdMembership.objects.filter(user_id=user_id).values("household_id"),
            deleted_at__isnull=False,
        )
        ordered = households.order_by("deleted_at", "name")
        return _to_deleted_households(ordered)

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
        households = Household.objects.filter(deleted_at__isnull=False, deleted_at__lte=cutoff)
        ordered = households.order_by("deleted_at", "name")
        return _to_deleted_households(ordered)

    def purge(self, household_ids: list[int]) -> None:
        Household.objects.filter(pk__in=household_ids).delete()


def _to_deleted_households(households: QuerySet[Household]) -> list[DeletedHousehold]:
    rows = households.annotate(number_of_members=Count("memberships"))
    deleted_households: list[DeletedHousehold] = []
    for row in rows:
        if row.deleted_at is None:
            raise HouseholdNotFoundError
        deleted_household = DeletedHousehold(
            id=row.pk, name=row.name, member_count=row.number_of_members, deleted_at=row.deleted_at
        )
        deleted_households.append(deleted_household)
    return deleted_households
