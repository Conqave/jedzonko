from households.application.access import HouseholdAccessPolicy
from households.application.ports.household_repository import HouseholdRepository
from households.infrastructure.django_household_repository import DjangoHouseholdRepository


def build_household_repository() -> HouseholdRepository:
    return DjangoHouseholdRepository()


def build_household_access_policy() -> HouseholdAccessPolicy:
    return HouseholdAccessPolicy(build_household_repository())
