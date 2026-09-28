from abc import ABC, abstractmethod
from datetime import datetime

from households.domain.alias_proposal import AliasProposal
from households.domain.alias_proposal_state import AliasProposalState


class AliasProposalRepository(ABC):
    @abstractmethod
    def list_pending(self, household_id: int) -> list[AliasProposal]:
        raise NotImplementedError

    @abstractmethod
    def list_pending_requirement_names(self, household_id: int) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def list_rejected_pairs(self, household_id: int) -> set[tuple[str, int]]:
        raise NotImplementedError

    @abstractmethod
    def find_proposal(self, proposal_id: int) -> AliasProposal | None:
        raise NotImplementedError

    @abstractmethod
    def create_proposal(
        self,
        household_id: int,
        requirement_name: str,
        normalized_requirement_name: str,
        product_id: int,
        model_name: str,
        created_at: datetime,
    ) -> AliasProposal:
        raise NotImplementedError

    @abstractmethod
    def set_state(self, proposal_id: int, state: AliasProposalState) -> AliasProposal:
        raise NotImplementedError
