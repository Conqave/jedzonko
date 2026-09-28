from dataclasses import dataclass
from datetime import datetime

from households.domain.tag_proposal_state import TagProposalState


@dataclass(frozen=True, slots=True)
class TagProposal:
    id: int
    household_id: int
    requirement_name: str
    normalized_requirement_name: str
    product_id: int
    product_name: str
    model_name: str
    created_at: datetime
    state: TagProposalState
