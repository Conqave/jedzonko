from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InventoryPhoto:
    filename: str
    content: bytes
