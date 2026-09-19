from datetime import datetime, timedelta, timezone

import pytest

from households.application.errors import (
    HouseholdNotFoundError,
    NotAHouseholdMemberError,
    RecoveryWindowExpiredError,
)
from households.application.use_cases.delete_household import DeleteHousehold
from households.application.use_cases.list_deleted_households import ListDeletedHouseholds
from households.application.use_cases.purge_expired_households import PurgeExpiredHouseholds
from households.application.use_cases.restore_household import RestoreHousehold
from households.domain.retention import HOUSEHOLD_RETENTION_PERIOD
from households.tests.fakes import FakeHouseholdLifecycleRepository, FakeHouseholdRow

MEMBER_ID = 1
OUTSIDER_ID = 2
HOUSEHOLD_ID = 10
NOW = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)


def _repository(deleted_at: datetime | None = None) -> FakeHouseholdLifecycleRepository:
    return FakeHouseholdLifecycleRepository(
        [FakeHouseholdRow(HOUSEHOLD_ID, "Dom", {MEMBER_ID}, deleted_at)]
    )


def test_delete_marks_the_household_deleted() -> None:
    repository = _repository()

    DeleteHousehold(repository).execute(MEMBER_ID, HOUSEHOLD_ID, NOW)

    assert repository.rows[0].deleted_at == NOW


def test_delete_rejects_a_non_member() -> None:
    repository = _repository()

    with pytest.raises(NotAHouseholdMemberError):
        DeleteHousehold(repository).execute(OUTSIDER_ID, HOUSEHOLD_ID, NOW)

    assert repository.rows[0].deleted_at is None


def test_delete_rejects_an_already_deleted_household() -> None:
    repository = _repository(NOW - timedelta(days=1))

    with pytest.raises(HouseholdNotFoundError):
        DeleteHousehold(repository).execute(MEMBER_ID, HOUSEHOLD_ID, NOW)


def test_restore_inside_the_window_clears_the_deletion() -> None:
    repository = _repository(NOW - HOUSEHOLD_RETENTION_PERIOD + timedelta(hours=1))

    summary = RestoreHousehold(repository).execute(MEMBER_ID, HOUSEHOLD_ID, NOW)

    assert summary.name == "Dom"
    assert repository.rows[0].deleted_at is None


def test_restore_outside_the_window_is_rejected() -> None:
    repository = _repository(NOW - HOUSEHOLD_RETENTION_PERIOD)

    with pytest.raises(RecoveryWindowExpiredError):
        RestoreHousehold(repository).execute(MEMBER_ID, HOUSEHOLD_ID, NOW)

    assert repository.rows[0].deleted_at is not None


def test_restore_rejects_a_non_member() -> None:
    repository = _repository(NOW - timedelta(days=1))

    with pytest.raises(NotAHouseholdMemberError):
        RestoreHousehold(repository).execute(OUTSIDER_ID, HOUSEHOLD_ID, NOW)


def test_restore_rejects_a_household_that_is_not_deleted() -> None:
    repository = _repository()

    with pytest.raises(HouseholdNotFoundError):
        RestoreHousehold(repository).execute(MEMBER_ID, HOUSEHOLD_ID, NOW)


def test_list_deleted_households_returns_only_the_members_deleted_households() -> None:
    deleted_at = NOW - timedelta(days=1)
    repository = FakeHouseholdLifecycleRepository(
        [
            FakeHouseholdRow(HOUSEHOLD_ID, "Dom", {MEMBER_ID}, deleted_at),
            FakeHouseholdRow(11, "Aktywny", {MEMBER_ID}, None),
            FakeHouseholdRow(12, "Obcy", {OUTSIDER_ID}, deleted_at),
        ]
    )

    households = ListDeletedHouseholds(repository).execute(MEMBER_ID)

    assert [household.id for household in households] == [HOUSEHOLD_ID]
    assert households[0].purge_after == deleted_at + HOUSEHOLD_RETENTION_PERIOD


def test_purge_removes_only_households_past_the_window() -> None:
    repository = FakeHouseholdLifecycleRepository(
        [
            FakeHouseholdRow(HOUSEHOLD_ID, "Stary", {MEMBER_ID}, NOW - HOUSEHOLD_RETENTION_PERIOD),
            FakeHouseholdRow(11, "Swiezy", {MEMBER_ID}, NOW - timedelta(days=1)),
            FakeHouseholdRow(12, "Aktywny", {MEMBER_ID}, None),
        ]
    )

    purged = PurgeExpiredHouseholds(repository).execute(NOW, False)

    assert [household.id for household in purged] == [HOUSEHOLD_ID]
    assert repository.purged == [HOUSEHOLD_ID]


def test_purge_dry_run_reports_without_deleting() -> None:
    repository = FakeHouseholdLifecycleRepository(
        [FakeHouseholdRow(HOUSEHOLD_ID, "Stary", {MEMBER_ID}, NOW - HOUSEHOLD_RETENTION_PERIOD)]
    )

    purged = PurgeExpiredHouseholds(repository).execute(NOW, True)

    assert [household.id for household in purged] == [HOUSEHOLD_ID]
    assert repository.purged == []
    assert len(repository.rows) == 1
