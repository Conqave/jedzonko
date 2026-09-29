from dataclasses import dataclass
from enum import StrEnum


class CurationDecision(StrEnum):
    NEW_TAG = "new_tag"
    ALIAS = "alias"
    DISMISS = "dismiss"


@dataclass(frozen=True, slots=True)
class CurationVerdict:
    candidate: str
    decision: CurationDecision
    alias_of: str | None

    def __post_init__(self) -> None:
        if (self.decision is CurationDecision.ALIAS) != (self.alias_of is not None):
            raise ValueError("Only an alias verdict names the tag it belongs to.")
