from households.application.access import HouseholdAccessPolicy
from households.application.ports.alias_proposal_repository import AliasProposalRepository
from households.domain.alias_proposal import AliasProposal


class ListAliasProposals:
    def __init__(self, repository: AliasProposalRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, household_id: int) -> list[AliasProposal]:
        self._access.require_membership(user_id, household_id)
        return self._repository.list_pending(household_id)
