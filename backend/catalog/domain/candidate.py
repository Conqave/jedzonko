from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from catalog.domain.ingredient import IngredientNameSource


class CandidateStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"


@dataclass(frozen=True, slots=True)
class IngredientNameCandidate:
    id: int
    name: str
    normalized_name: str
    source: IngredientNameSource
    status: CandidateStatus
    decided_at: datetime | None


@dataclass(frozen=True, slots=True)
class ImportReport:
    created: tuple[str, ...]
    already_known: tuple[str, ...]
    already_candidates: tuple[str, ...]
