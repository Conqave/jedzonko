from datetime import datetime

from catalog.application.errors import (
    CandidateAlreadyDecidedError,
    CandidateNotFoundError,
    DuplicateIngredientNameError,
    IngredientNotFoundError,
)
from catalog.application.ports.candidate_repository import CandidateRepository
from catalog.application.ports.ingredient_repository import IngredientRepository
from catalog.domain.candidate import CandidateStatus, IngredientNameCandidate
from catalog.domain.ingredient import IngredientNameKind
from catalog.domain.names import CatalogName
from shared.transactions import TransactionManager


class _CandidateDecision:
    def __init__(
        self,
        candidates: CandidateRepository,
        ingredients: IngredientRepository,
        transactions: TransactionManager,
    ) -> None:
        self._candidates = candidates
        self._ingredients = ingredients
        self._transactions = transactions

    def _pending(self, candidate_id: int) -> IngredientNameCandidate:
        candidate = self._candidates.find(candidate_id)
        if candidate is None:
            raise CandidateNotFoundError
        if candidate.status is not CandidateStatus.PENDING:
            raise CandidateAlreadyDecidedError
        return candidate

    def _name_is_free(self, candidate: IngredientNameCandidate) -> CatalogName:
        text = CatalogName.parse(candidate.name)
        if self._ingredients.find_by_normalized_name(text.normalized_name) is not None:
            raise DuplicateIngredientNameError
        return text


class AcceptCandidateAsIngredient(_CandidateDecision):
    def execute(self, candidate_id: int, now: datetime) -> None:
        with self._transactions.atomic():
            candidate = self._pending(candidate_id)
            name = self._name_is_free(candidate)
            self._ingredients.create(name, candidate.source)
            self._candidates.decide(candidate_id, CandidateStatus.ACCEPTED, now)


class AcceptCandidateAsAlias(_CandidateDecision):
    def execute(self, candidate_id: int, ingredient_id: int, now: datetime) -> None:
        with self._transactions.atomic():
            candidate = self._pending(candidate_id)
            if self._ingredients.find(ingredient_id) is None:
                raise IngredientNotFoundError
            name = self._name_is_free(candidate)
            self._ingredients.add_name(
                ingredient_id,
                name,
                IngredientNameKind.ALIAS,
                candidate.source,
            )
            self._candidates.decide(candidate_id, CandidateStatus.ACCEPTED, now)


class DismissCandidate(_CandidateDecision):
    def execute(self, candidate_id: int, now: datetime) -> None:
        with self._transactions.atomic():
            self._pending(candidate_id)
            self._candidates.decide(candidate_id, CandidateStatus.DISMISSED, now)
