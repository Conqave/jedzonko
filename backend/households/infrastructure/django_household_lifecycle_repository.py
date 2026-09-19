from datetime import datetime

from django.db import models, transaction
from django.db.models import Count

from households.application.errors import HouseholdNotFoundError
from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.domain.deleted_household import DeletedHousehold
from households.domain.models import HouseholdSummary
from households.models import Household, HouseholdMembership, Product


class DjangoHouseholdLifecycleRepository(HouseholdLifecycleRepository):
    def is_member(self, user_id: int, household_id: int) -> bool:
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
            Household.objects.filter(memberships__user_id=user_id, deleted_at__isnull=False)
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

    @transaction.atomic
    def purge(self, household_ids: list[int]) -> None:
        _delete_rows_protecting_products(household_ids)
        Household.objects.filter(pk__in=household_ids).delete()


def _delete_rows_protecting_products(household_ids: list[int]) -> None:
    # Django refuses a cascading delete while any PROTECT reference to the cascaded
    # products still exists, even when those referencing rows are cascaded away too.
    product_ids = list(
        Product.objects.filter(household_id__in=household_ids).values_list("pk", flat=True)
    )
    if not product_ids:
        return
    for relation in Product._meta.related_objects:
        if relation.on_delete is not models.PROTECT:
            continue
        relation.related_model._default_manager.filter(
            **{f"{relation.field.name}__in": product_ids}
        ).delete()


def _to_deleted_household(
    household_id: int, name: str, member_count: int, deleted_at: datetime | None
) -> DeletedHousehold:
    if deleted_at is None:
        raise HouseholdNotFoundError
    return DeletedHousehold(
        id=household_id, name=name, member_count=member_count, deleted_at=deleted_at
    )
