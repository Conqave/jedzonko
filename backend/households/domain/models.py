from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HouseholdSummary:
    id: int
    name: str
    member_count: int


@dataclass(frozen=True, slots=True)
class HouseholdMember:
    user_id: int
    username: str
