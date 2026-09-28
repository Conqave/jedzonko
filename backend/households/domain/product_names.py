from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductNames:
    id: int
    name: str
    normalized_name: str
    tag_names: tuple[str, ...]
