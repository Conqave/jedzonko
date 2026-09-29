from abc import ABC, abstractmethod

from catalog.domain.curation import CurationVerdict


class CandidateCurator(ABC):
    @abstractmethod
    def curate(
        self, candidate_names: tuple[str, ...], tag_names: tuple[str, ...]
    ) -> tuple[CurationVerdict, ...]:
        raise NotImplementedError
