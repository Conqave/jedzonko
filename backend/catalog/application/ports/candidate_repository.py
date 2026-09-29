from abc import ABC, abstractmethod
from datetime import datetime

from catalog.domain.candidate import CandidateStatus, IngredientNameCandidate
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import CatalogName


class CandidateRepository(ABC):
    @abstractmethod
    def find(self, candidate_id: int) -> IngredientNameCandidate | None:
        raise NotImplementedError

    @abstractmethod
    def existing_normalized_names(self, normalized_names: set[str]) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def create(self, name: CatalogName, source: IngredientNameSource) -> IngredientNameCandidate:
        raise NotImplementedError

    @abstractmethod
    def decide(self, candidate_id: int, status: CandidateStatus, decided_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_pending(self) -> list[IngredientNameCandidate]:
        raise NotImplementedError
