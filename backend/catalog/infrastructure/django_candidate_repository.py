from datetime import datetime

from catalog.application.errors import CandidateNotFoundError
from catalog.application.ports.candidate_repository import CandidateRepository
from catalog.domain.candidate import CandidateStatus, IngredientNameCandidate
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.models import IngredientNameCandidate as CandidateRow


class DjangoCandidateRepository(CandidateRepository):
    def find(self, candidate_id: int) -> IngredientNameCandidate | None:
        row = CandidateRow.objects.filter(pk=candidate_id).first()
        return None if row is None else _to_candidate(row)

    def existing_normalized_names(self, normalized_names: set[str]) -> set[str]:
        rows = CandidateRow.objects.filter(normalized_name__in=normalized_names)
        existing = rows.values_list("normalized_name", flat=True)
        return set(existing)

    def create(self, name: CatalogName, source: IngredientNameSource) -> IngredientNameCandidate:
        row = CandidateRow.objects.create(
            name=name.name,
            normalized_name=name.normalized_name,
            source=source.value,
            status=CandidateStatus.PENDING.value,
        )
        return _to_candidate(row)

    def decide(self, candidate_id: int, status: CandidateStatus, decided_at: datetime) -> None:
        updated = CandidateRow.objects.filter(pk=candidate_id).update(
            status=status.value, decided_at=decided_at
        )
        if updated == 0:
            raise CandidateNotFoundError


def _to_candidate(row: CandidateRow) -> IngredientNameCandidate:
    return IngredientNameCandidate(
        id=row.pk,
        name=row.name,
        normalized_name=row.normalized_name,
        source=IngredientNameSource(row.source),
        status=CandidateStatus(row.status),
        decided_at=row.decided_at,
    )
