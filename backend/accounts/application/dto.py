from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: int
    username: str
    is_staff: bool
    can_view_promotions: bool
