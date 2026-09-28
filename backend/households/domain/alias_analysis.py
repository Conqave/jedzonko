from dataclasses import dataclass

from households.domain.alias_proposal import AliasProposal


@dataclass(frozen=True, slots=True)
class HouseholdAliasAnalysis:
    household_id: int
    household_name: str
    unmatched_requirement_count: int
    question_count: int
    proposals: tuple[AliasProposal, ...]


@dataclass(frozen=True, slots=True)
class AliasAnalysisReport:
    households: tuple[HouseholdAliasAnalysis, ...]
    question_count: int
    question_limit: int
    limit_reached: bool
    failure: str | None
