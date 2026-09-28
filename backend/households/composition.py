from households.application.access import HouseholdAccessPolicy
from households.application.ports.alias_proposal_repository import AliasProposalRepository
from households.application.ports.household_lifecycle_repository import (
    HouseholdLifecycleRepository,
)
from households.application.ports.household_repository import HouseholdRepository
from households.application.ports.product_alias_repository import ProductTagRepository
from households.application.ports.product_repository import ProductRepository
from households.application.ports.transaction_manager import TransactionManager
from households.application.use_cases.accept_alias_proposal import AcceptAliasProposal
from households.application.use_cases.create_household_product import CreateHouseholdProduct
from households.application.use_cases.delete_household import DeleteHousehold
from households.application.use_cases.find_household_product import FindHouseholdProduct
from households.application.use_cases.list_alias_proposals import ListAliasProposals
from households.application.use_cases.list_deleted_households import ListDeletedHouseholds
from households.application.use_cases.list_household_products import ListHouseholdProducts
from households.application.use_cases.list_measurement_units import ListMeasurementUnits
from households.application.use_cases.purge_expired_households import PurgeExpiredHouseholds
from households.application.use_cases.reject_alias_proposal import RejectAliasProposal
from households.application.use_cases.rename_household import RenameHousehold
from households.application.use_cases.rename_household_product import RenameHouseholdProduct
from households.application.use_cases.resolve_household_product import ResolveHouseholdProduct
from households.application.use_cases.restore_household import RestoreHousehold
from households.infrastructure.django_alias_proposal_repository import (
    DjangoAliasProposalRepository,
)
from households.infrastructure.django_household_lifecycle_repository import (
    DjangoHouseholdLifecycleRepository,
)
from households.infrastructure.django_household_repository import DjangoHouseholdRepository
from households.infrastructure.django_product_alias_repository import DjangoProductTagRepository
from households.infrastructure.django_product_repository import DjangoProductRepository
from households.infrastructure.django_transaction_manager import DjangoTransactionManager


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


def build_rename_household_product() -> RenameHouseholdProduct:
    return RenameHouseholdProduct(build_product_repository(), build_household_access_policy())


def build_resolve_household_product() -> ResolveHouseholdProduct:
    return ResolveHouseholdProduct(build_product_repository())


def build_find_household_product() -> FindHouseholdProduct:
    return FindHouseholdProduct(build_product_repository())


def build_list_measurement_units() -> ListMeasurementUnits:
    return ListMeasurementUnits()


def build_rename_household() -> RenameHousehold:
    return RenameHousehold(build_household_repository(), build_household_access_policy())


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


def build_alias_proposal_repository() -> AliasProposalRepository:
    return DjangoAliasProposalRepository()


def build_product_tag_repository() -> ProductTagRepository:
    return DjangoProductTagRepository()


def build_transaction_manager() -> TransactionManager:
    return DjangoTransactionManager()


def build_list_alias_proposals() -> ListAliasProposals:
    return ListAliasProposals(build_alias_proposal_repository(), build_household_access_policy())


def build_accept_alias_proposal() -> AcceptAliasProposal:
    return AcceptAliasProposal(
        build_alias_proposal_repository(),
        build_product_tag_repository(),
        build_transaction_manager(),
        build_household_access_policy(),
    )


def build_reject_alias_proposal() -> RejectAliasProposal:
    return RejectAliasProposal(build_alias_proposal_repository(), build_household_access_policy())


def build_tag_proposal_repository() -> AliasProposalRepository:
    return build_alias_proposal_repository()


def build_list_tag_proposals() -> ListAliasProposals:
    return ListAliasProposals(build_tag_proposal_repository(), build_household_access_policy())


def build_accept_tag_proposal() -> AcceptAliasProposal:
    return AcceptAliasProposal(
        build_tag_proposal_repository(),
        build_product_tag_repository(),
        build_transaction_manager(),
        build_household_access_policy(),
    )


def build_reject_tag_proposal() -> RejectAliasProposal:
    return RejectAliasProposal(build_tag_proposal_repository(), build_household_access_policy())
