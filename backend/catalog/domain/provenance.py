from dataclasses import dataclass
from enum import StrEnum

from catalog.domain.errors import InvalidFactProvenanceError

MAX_REFERENCE_URL_LENGTH = 500


class FactSource(StrEnum):
    MANUAL = "manual"
    REFERENCE = "reference"


class ReferenceImportDecision(StrEnum):
    UPDATE = "update"
    UNCHANGED = "unchanged"
    KEEP_MANUAL = "keep_manual"


@dataclass(frozen=True, slots=True)
class Provenance:
    source: FactSource
    reference_url: str | None

    def __post_init__(self) -> None:
        has_reference = self.reference_url is not None
        if has_reference is not (self.source is FactSource.REFERENCE):
            raise InvalidFactProvenanceError("Exactly the reference values carry a source URL.")
        if self.reference_url is not None and not self.reference_url.strip():
            raise InvalidFactProvenanceError("The source URL is empty.")
        if self.reference_url is not None and len(self.reference_url) > MAX_REFERENCE_URL_LENGTH:
            raise InvalidFactProvenanceError(
                f"The source URL is longer than {MAX_REFERENCE_URL_LENGTH} characters."
            )

    @classmethod
    def manual(cls) -> Provenance:
        return cls(source=FactSource.MANUAL, reference_url=None)

    @classmethod
    def from_reference(cls, reference_url: str) -> Provenance:
        return cls(source=FactSource.REFERENCE, reference_url=reference_url)

    @property
    def is_manual(self) -> bool:
        return self.source is FactSource.MANUAL

    @property
    def is_reference(self) -> bool:
        return self.source is FactSource.REFERENCE


def decide_reference_import(
    current: Provenance | None, is_unchanged: bool
) -> ReferenceImportDecision:
    if current is not None and current.is_manual:
        return ReferenceImportDecision.KEEP_MANUAL
    if is_unchanged:
        return ReferenceImportDecision.UNCHANGED
    return ReferenceImportDecision.UPDATE
