from dataclasses import dataclass
from datetime import datetime

from catalog.application.errors import (
    CandidateAlreadyDecidedError,
    DuplicateIngredientNameError,
    IngredientClassifierContractError,
)
from catalog.application.ports.candidate_curator import CandidateCurator
from catalog.application.ports.candidate_repository import CandidateRepository
from catalog.application.use_cases.decide_candidate import (
    AcceptCandidateAsAlias,
    AcceptCandidateAsIngredient,
    DismissCandidate,
)
from catalog.application.use_cases.list_tags import ListTags
from catalog.domain.candidate import IngredientNameCandidate
from catalog.domain.curation import CurationDecision, CurationVerdict


@dataclass(frozen=True, slots=True)
class CurationRun:
    new_tags: tuple[str, ...]
    aliases: tuple[str, ...]
    dismissed: tuple[str, ...]
    skipped: tuple[str, ...]


class _RunLog:
    def __init__(self) -> None:
        self.new_tags: list[str] = []
        self.aliases: list[str] = []
        self.dismissed: list[str] = []
        self.skipped: list[str] = []

    def freeze(self) -> CurationRun:
        return CurationRun(
            new_tags=tuple(self.new_tags),
            aliases=tuple(self.aliases),
            dismissed=tuple(self.dismissed),
            skipped=tuple(self.skipped),
        )


class CurateCandidates:
    def __init__(
        self,
        candidates: CandidateRepository,
        list_tags: ListTags,
        curator: CandidateCurator,
        accept_as_tag: AcceptCandidateAsIngredient,
        accept_as_alias: AcceptCandidateAsAlias,
        dismiss: DismissCandidate,
        batch_size: int,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        self._candidates = candidates
        self._list_tags = list_tags
        self._curator = curator
        self._accept_as_tag = accept_as_tag
        self._accept_as_alias = accept_as_alias
        self._dismiss = dismiss
        self._batch_size = batch_size

    def execute(self, now: datetime, candidate_limit: int) -> CurationRun:
        pending = self._candidates.list_pending()[:candidate_limit]
        run = _RunLog()
        for start in range(0, len(pending), self._batch_size):
            batch = pending[start : start + self._batch_size]
            self._curate_batch(batch, now, run)
        return run.freeze()

    def _curate_batch(
        self, batch: list[IngredientNameCandidate], now: datetime, run: _RunLog
    ) -> None:
        tags = self._list_tags.execute()
        tag_ids = {tag.name: tag.id for tag in tags}
        names = tuple(candidate.name for candidate in batch)
        try:
            verdicts = self._curator.curate(names, tuple(tag_ids))
        except IngredientClassifierContractError as error:
            run.skipped.extend(f"{name}: {error}" for name in names)
            return
        by_name = {verdict.candidate: verdict for verdict in verdicts}
        answered = [
            (candidate, by_name[candidate.name]) for candidate in batch if candidate.name in by_name
        ]
        run.skipped.extend(
            f"{candidate.name}: no verdict" for candidate in batch if candidate.name not in by_name
        )
        first = [pair for pair in answered if pair[1].decision is not CurationDecision.ALIAS]
        aliases = [pair for pair in answered if pair[1].decision is CurationDecision.ALIAS]
        for candidate, verdict in first:
            self._apply(candidate, verdict, tag_ids, now, run)
        refreshed = self._list_tags.execute()
        refreshed_ids = {tag.name: tag.id for tag in refreshed}
        for candidate, verdict in aliases:
            self._apply(candidate, verdict, refreshed_ids, now, run)

    def _apply(
        self,
        candidate: IngredientNameCandidate,
        verdict: CurationVerdict,
        tag_ids: dict[str, int],
        now: datetime,
        run: _RunLog,
    ) -> None:
        try:
            if verdict.decision is CurationDecision.DISMISS:
                self._dismiss.execute(candidate.id, now)
                run.dismissed.append(candidate.name)
            elif verdict.decision is CurationDecision.NEW_TAG:
                self._accept_as_tag.execute(candidate.id, now)
                run.new_tags.append(candidate.name)
            else:
                target_id = tag_ids.get(verdict.alias_of or "")
                if target_id is None:
                    run.skipped.append(f"{candidate.name}: unknown tag {verdict.alias_of!r}")
                    return
                self._accept_as_alias.execute(candidate.id, target_id, now)
                run.aliases.append(f"{candidate.name} -> {verdict.alias_of}")
        except (DuplicateIngredientNameError, CandidateAlreadyDecidedError) as error:
            run.skipped.append(f"{candidate.name}: {type(error).__name__}")
