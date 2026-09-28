from datetime import UTC, datetime

import pytest

from catalog.application.errors import (
    CandidateAlreadyDecidedError,
    CandidateNotFoundError,
    DuplicateIngredientNameError,
)
from catalog.application.use_cases.decide_candidate import (
    AcceptCandidateAsAlias,
    AcceptCandidateAsIngredient,
    DismissCandidate,
)
from catalog.application.use_cases.find_ingredient_by_name import FindIngredientByName
from catalog.application.use_cases.import_ingredient_names import ImportIngredientNames
from catalog.domain.candidate import CandidateStatus
from catalog.domain.ingredient import IngredientNameKind, IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.tests.fakes import (
    FakeCandidateRepository,
    FakeIngredientRepository,
    FakeTransactionManager,
)

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
PROVIDER = IngredientNameSource.ANIA_GOTUJE


class Setup:
    def __init__(self) -> None:
        self.transactions = FakeTransactionManager()
        self.ingredients = FakeIngredientRepository()
        self.candidates = FakeCandidateRepository()
        eggs = CatalogName.parse("Jajka")
        self.eggs = self.ingredients.create(eggs, IngredientNameSource.MANUAL).id

    def import_names(self, *names: str) -> None:
        use_case = ImportIngredientNames(self.ingredients, self.candidates, self.transactions)
        use_case.execute(names, PROVIDER)

    def candidate_id(self, name: str) -> int:
        for candidate in self.candidates.candidates.values():
            if candidate.name == name:
                return candidate.id
        raise AssertionError(f"No candidate {name!r}.")


@pytest.fixture
def setup() -> Setup:
    return Setup()


def test_importing_queues_only_new_names(setup: Setup) -> None:
    setup.import_names("cukinia")
    use_case = ImportIngredientNames(setup.ingredients, setup.candidates, setup.transactions)

    report = use_case.execute(("JAJKA", "cukinia", "bakłażan", "Bakłażan "), PROVIDER)

    assert report.created == ("bakłażan",)
    assert report.already_known == ("JAJKA",)
    assert report.already_candidates == ("cukinia",)


def test_a_queued_name_does_not_resolve_until_accepted(setup: Setup) -> None:
    setup.import_names("cukinia")
    find_by_name = FindIngredientByName(setup.ingredients)

    before = find_by_name.execute("cukinia")
    accept = AcceptCandidateAsIngredient(setup.candidates, setup.ingredients, setup.transactions)
    accept.execute(setup.candidate_id("cukinia"), NOW)
    after = find_by_name.execute("cukinia")

    assert before is None
    assert after is not None and after.name == "cukinia"


def test_accepting_as_an_alias_names_an_existing_ingredient(setup: Setup) -> None:
    setup.import_names("jaja")
    accept = AcceptCandidateAsAlias(setup.candidates, setup.ingredients, setup.transactions)

    accept.execute(setup.candidate_id("jaja"), setup.eggs, NOW)

    alias = [name for name in setup.ingredients.names if name.normalized_name == "jaja"]
    assert [(name.ingredient_id, name.kind) for name in alias] == [
        (setup.eggs, IngredientNameKind.ALIAS)
    ]


def test_a_dismissed_candidate_stays_decided(setup: Setup) -> None:
    setup.import_names("dla dzieci")
    candidate_id = setup.candidate_id("dla dzieci")
    dismiss = DismissCandidate(setup.candidates, setup.ingredients, setup.transactions)

    dismiss.execute(candidate_id, NOW)

    candidate = setup.candidates.find(candidate_id)
    assert candidate is not None and candidate.status is CandidateStatus.DISMISSED
    with pytest.raises(CandidateAlreadyDecidedError):
        dismiss.execute(candidate_id, NOW)


def test_a_candidate_whose_name_became_an_ingredient_cannot_be_accepted(setup: Setup) -> None:
    setup.import_names("cukinia")
    setup.ingredients.create(CatalogName.parse("Cukinia"), IngredientNameSource.MANUAL)
    accept = AcceptCandidateAsIngredient(setup.candidates, setup.ingredients, setup.transactions)

    with pytest.raises(DuplicateIngredientNameError):
        accept.execute(setup.candidate_id("cukinia"), NOW)


def test_an_unknown_candidate_is_reported(setup: Setup) -> None:
    dismiss = DismissCandidate(setup.candidates, setup.ingredients, setup.transactions)

    with pytest.raises(CandidateNotFoundError):
        dismiss.execute(404, NOW)
