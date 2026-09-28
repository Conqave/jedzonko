import re

from recipes.application.errors import RecipeSourceContractError

_ISO_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


def parse_iso_duration_minutes(value: str) -> int:
    match = _ISO_DURATION.match(value.strip())
    if match is None or not any(match.groups()):
        raise RecipeSourceContractError(f"Unsupported ISO 8601 duration: {value!r}")
    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return days * 24 * 60 + hours * 60 + minutes + seconds // 60
