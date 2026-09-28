from households.application.access import HouseholdAccessPolicy
from households.application.errors import (
    AliasProposalNotFoundError,
    AliasProposalNotPendingError,
)
from households.application.ports.alias_proposal_repository import AliasProposalRepository
from households.domain.alias_proposal import AliasProposal
from households.domain.alias_proposal_state import AliasProposalState


class RejectAliasProposal:
    def __init__(self, repository: AliasProposalRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, proposal_id: int) -> AliasProposal:
        proposal = self._repository.find_proposal(proposal_id)
        if proposal is None:
            raise AliasProposalNotFoundError
        self._access.require_membership(user_id, proposal.household_id)
        if proposal.state is not AliasProposalState.PENDING:
            raise AliasProposalNotPendingError
        return self._repository.set_state(proposal_id, AliasProposalState.REJECTED)
