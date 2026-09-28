from datetime import datetime

from households.application.errors import AliasProposalNotFoundError
from households.application.ports.alias_proposal_repository import AliasProposalRepository
from households.domain.alias_proposal import AliasProposal
from households.domain.alias_proposal_state import AliasProposalState
from households.models import TagProposal


class DjangoAliasProposalRepository(AliasProposalRepository):
    def list_pending(self, household_id: int) -> list[AliasProposal]:
        rows = TagProposal.objects.filter(
            household_id=household_id, state=AliasProposalState.PENDING
        ).select_related("product")
        return [self._to_proposal(row) for row in rows]

    def list_pending_requirement_names(self, household_id: int) -> set[str]:
        rows = TagProposal.objects.filter(
            household_id=household_id, state=AliasProposalState.PENDING
        ).values_list("normalized_requirement_name", flat=True)
        return set(rows)

    def list_rejected_pairs(self, household_id: int) -> set[tuple[str, int]]:
        rows = TagProposal.objects.filter(
            household_id=household_id, state=AliasProposalState.REJECTED
        ).values_list("normalized_requirement_name", "product_id")
        return {(name, product_id) for name, product_id in rows}

    def find_proposal(self, proposal_id: int) -> AliasProposal | None:
        row = (
            TagProposal.objects.filter(pk=proposal_id).select_related("product").first()
        )
        return None if row is None else self._to_proposal(row)

    def create_proposal(
        self,
        household_id: int,
        requirement_name: str,
        normalized_requirement_name: str,
        product_id: int,
        model_name: str,
        created_at: datetime,
    ) -> AliasProposal:
        row, _ = TagProposal.objects.get_or_create(
            household_id=household_id,
            normalized_requirement_name=normalized_requirement_name,
            product_id=product_id,
            defaults={
                "requirement_name": requirement_name,
                "model_name": model_name,
                "state": AliasProposalState.PENDING,
                "created_at": created_at,
            },
        )
        return self._to_proposal(row)

    def set_state(self, proposal_id: int, state: AliasProposalState) -> AliasProposal:
        row = (
            TagProposal.objects.filter(pk=proposal_id).select_related("product").first()
        )
        if row is None:
            raise AliasProposalNotFoundError
        row.state = state
        row.save(update_fields=["state"])
        return self._to_proposal(row)

    @staticmethod
    def _to_proposal(row: TagProposal) -> AliasProposal:
        return AliasProposal(
            id=row.pk,
            household_id=row.household_id,
            requirement_name=row.requirement_name,
            normalized_requirement_name=row.normalized_requirement_name,
            product_id=row.product_id,
            product_name=row.product.name,
            model_name=row.model_name,
            created_at=row.created_at,
            state=AliasProposalState(row.state),
        )
