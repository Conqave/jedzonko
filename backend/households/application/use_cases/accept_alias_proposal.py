from households.application.access import HouseholdAccessPolicy
from households.application.errors import (
    AliasProposalNotFoundError,
    AliasProposalNotPendingError,
)
from households.application.ports.alias_proposal_repository import AliasProposalRepository
from households.application.ports.product_alias_repository import ProductTagRepository
from households.application.ports.transaction_manager import TransactionManager
from households.domain.alias_proposal import AliasProposal
from households.domain.alias_proposal_state import AliasProposalState


class AcceptAliasProposal:
    def __init__(
        self,
        repository: AliasProposalRepository,
        tag_repository: ProductTagRepository,
        transaction_manager: TransactionManager,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._repository = repository
        self._tag_repository = tag_repository
        self._transaction_manager = transaction_manager
        self._access = access

    def execute(self, user_id: int, proposal_id: int) -> AliasProposal:
        proposal = self._repository.find_proposal(proposal_id)
        if proposal is None:
            raise AliasProposalNotFoundError
        self._access.require_membership(user_id, proposal.household_id)
        if proposal.state is not AliasProposalState.PENDING:
            raise AliasProposalNotPendingError
        with self._transaction_manager.atomic():
            self._tag_repository.create_tag(proposal.product_id, proposal.requirement_name, "ollama")
            return self._repository.set_state(proposal_id, AliasProposalState.ACCEPTED)
