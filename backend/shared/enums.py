from enum import StrEnum


def enum_values(enum: type[StrEnum]) -> list[str]:
    return [member.value for member in enum]


def enum_choices(enum: type[StrEnum]) -> list[tuple[str, str]]:
    return [(value, value) for value in enum_values(enum)]
