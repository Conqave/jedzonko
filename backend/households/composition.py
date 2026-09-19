from households.application.access import HouseholdAccessPolicy
from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.application.ports.household_repository import HouseholdRepository
from households.application.ports.product_repository import ProductRepository
from households.application.use_cases.create_household_product import CreateHouseholdProduct
from households.application.use_cases.delete_household import DeleteHousehold
from households.application.use_cases.find_household_product import FindHouseholdProduct
from households.application.use_cases.list_deleted_households import ListDeletedHouseholds
from households.application.use_cases.list_household_products import ListHouseholdProducts
from households.application.use_cases.list_measurement_units import ListMeasurementUnits
from households.application.use_cases.purge_expired_households import PurgeExpiredHouseholds
from households.application.use_cases.resolve_household_product import ResolveHouseholdProduct
from households.application.use_cases.restore_household import RestoreHousehold
from households.infrastructure.django_household_lifecycle_repository import (
    DjangoHouseholdLifecycleRepository,
)
from households.infrastructure.django_household_repository import DjangoHouseholdRepository
from households.infrastructure.django_product_repository import DjangoProductRepository


def build_household_repository() -> HouseholdRepository:
    return DjangoHouseholdRepository()


def build_household_access_policy() -> HouseholdAccessPolicy:
    return HouseholdAccessPolicy(build_household_repository())


def build_product_repository() -> ProductRepository:
    return DjangoProductRepository()


def build_list_household_products() -> ListHouseholdProducts:
    return ListHouseholdProducts(build_product_repository(), build_household_access_policy())


def build_create_household_product() -> CreateHouseholdProduct:
    return CreateHouseholdProduct(build_product_repository(), build_household_access_policy())


def build_resolve_household_product() -> ResolveHouseholdProduct:
    return ResolveHouseholdProduct(build_product_repository())


def build_find_household_product() -> FindHouseholdProduct:
    return FindHouseholdProduct(build_product_repository())


def build_list_measurement_units() -> ListMeasurementUnits:
    return ListMeasurementUnits()


def build_household_lifecycle_repository() -> HouseholdLifecycleRepository:
    return DjangoHouseholdLifecycleRepository()


def build_delete_household() -> DeleteHousehold:
    return DeleteHousehold(build_household_lifecycle_repository())


def build_restore_household() -> RestoreHousehold:
    return RestoreHousehold(build_household_lifecycle_repository())


def build_list_deleted_households() -> ListDeletedHouseholds:
    return ListDeletedHouseholds(build_household_lifecycle_repository())


def build_purge_expired_households() -> PurgeExpiredHouseholds:
    return PurgeExpiredHouseholds(build_household_lifecycle_repository())
