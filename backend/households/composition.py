from dataclasses import dataclass

from households.application.ports.household_provisioner import HouseholdProvisioner
from households.application.use_cases.add_household_member import AddHouseholdMember
from households.application.use_cases.create_household import CreateHousehold
from households.application.use_cases.delete_household import DeleteHousehold
from households.application.use_cases.list_deleted_households import ListDeletedHouseholds
from households.application.use_cases.list_household_members import ListHouseholdMembers
from households.application.use_cases.list_user_households import ListUserHouseholds
from households.application.use_cases.purge_expired_households import PurgeExpiredHouseholds
from households.application.use_cases.remove_household_member import RemoveHouseholdMember
from households.application.use_cases.rename_household import RenameHousehold
from households.application.use_cases.restore_household import RestoreHousehold
from households.infrastructure.django_household_lifecycle_repository import (
    DjangoHouseholdLifecycleRepository,
)
from households.infrastructure.django_household_repository import DjangoHouseholdRepository
from shared.household_membership import HouseholdMembershipReader
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class HouseholdsModule:
    list_user_households: ListUserHouseholds
    create_household: CreateHousehold
    rename_household: RenameHousehold
    delete_household: DeleteHousehold
    restore_household: RestoreHousehold
    list_deleted_households: ListDeletedHouseholds
    purge_expired_households: PurgeExpiredHouseholds
    list_household_members: ListHouseholdMembers
    add_household_member: AddHouseholdMember
    remove_household_member: RemoveHouseholdMember


def build_membership_reader() -> HouseholdMembershipReader:
    return DjangoHouseholdRepository()


def build_households(
    provisioner: HouseholdProvisioner, transactions: TransactionManager
) -> HouseholdsModule:
    repository = DjangoHouseholdRepository()
    lifecycle = DjangoHouseholdLifecycleRepository()
    memberships = repository
    return HouseholdsModule(
        list_user_households=ListUserHouseholds(repository),
        create_household=CreateHousehold(repository, provisioner, transactions),
        rename_household=RenameHousehold(repository, memberships),
        delete_household=DeleteHousehold(lifecycle),
        restore_household=RestoreHousehold(lifecycle),
        list_deleted_households=ListDeletedHouseholds(lifecycle),
        purge_expired_households=PurgeExpiredHouseholds(lifecycle),
        list_household_members=ListHouseholdMembers(repository, memberships),
        add_household_member=AddHouseholdMember(repository, memberships),
        remove_household_member=RemoveHouseholdMember(repository, memberships),
    )
