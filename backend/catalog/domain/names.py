from dataclasses import dataclass

from catalog.domain.errors import InvalidNameError
from shared.text import normalize_text

MAX_NAME_LENGTH = 120


@dataclass(frozen=True, slots=True)
class CatalogName:

    name: str
    normalized_name: str

    @classmethod
    def parse(cls, raw_name: str) -> CatalogName:
        name = " ".join(raw_name.split())
        normalized_name = normalize_text(name)
        if not normalized_name:
            raise InvalidNameError("The name is empty.")
        if max(len(name), len(normalized_name)) > MAX_NAME_LENGTH:
            raise InvalidNameError(f"The name is longer than {MAX_NAME_LENGTH} characters.")
        return cls(name=name, normalized_name=normalized_name)
