from datetime import UTC, datetime

from catalog.application.ports.candidate_curator import CandidateCurator
from catalog.application.use_cases.curate_candidates import CurateCandidates
from catalog.application.use_cases.decide_candidate import (
    AcceptCandidateAsAlias,
    AcceptCandidateAsIngredient,
    DismissCandidate,
)
from catalog.application.use_cases.list_tags import ListTags
from catalog.domain.curation import CurationDecision, CurationVerdict
from catalog.domain.ingredient import IngredientNameKind, IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.tests.fakes import (
    FakeCandidateRepository,
    FakeIngredientRepository,
    FakeTransactionManager,
)

NOW = datetime(2026, 9, 29, 22, 0, tzinfo=UTC)
SOURCE = IngredientNameSource.ANIA_GOTUJE


class ScriptedCurator(CandidateCurator):
    def __init__(self, verdicts: tuple[CurationVerdict, ...]) -> None:
        self._verdicts = verdicts
        self.dictionaries: list[tuple[str, ...]] = []

    def curate(
        self, candidate_names: tuple[str, ...], tag_names: tuple[str, ...]
    ) -> tuple[CurationVerdict, ...]:
        self.dictionaries.append(tag_names)
        return tuple(verdict for verdict in self._verdicts if verdict.candidate in candidate_names)


def _curation(
    curator: CandidateCurator, candidates: tuple[str, ...]
) -> tuple[CurateCandidates, FakeIngredientRepository]:
    ingredients = FakeIngredientRepository()
    ingredients.create(CatalogName.parse("jajka"), SOURCE)
    repository = FakeCandidateRepository()
    for name in candidates:
        repository.create(CatalogName.parse(name), SOURCE)
    transactions = FakeTransactionManager()
    use_case = CurateCandidates(
        repository,
        ListTags(ingredients),
        curator,
        AcceptCandidateAsIngredient(repository, ingredients, transactions),
        AcceptCandidateAsAlias(repository, ingredients, transactions),
        DismissCandidate(repository, ingredients, transactions),
        batch_size=10,
    )
    return use_case, ingredients


def _names(ingredients: FakeIngredientRepository, kind: IngredientNameKind) -> list[str]:
    return sorted(name.name for name in ingredients.list_names() if name.kind is kind)


def test_candidates_become_tags_aliases_or_are_dismissed() -> None:
    curator = ScriptedCurator(
        (
            CurationVerdict("jajko", CurationDecision.ALIAS, "jajka"),
            CurationVerdict("dynia", CurationDecision.NEW_TAG, None),
            CurationVerdict("dla dzieci", CurationDecision.DISMISS, None),
        )
    )
    use_case, ingredients = _curation(curator, ("jajko", "dynia", "dla dzieci"))

    run = use_case.execute(NOW, 100)

    assert (run.new_tags, run.aliases, run.dismissed) == (
        ("dynia",),
        ("jajko -> jajka",),
        ("dla dzieci",),
    )
    assert _names(ingredients, IngredientNameKind.CANONICAL) == ["dynia", "jajka"]
    assert _names(ingredients, IngredientNameKind.ALIAS) == ["jajko"]


def test_an_alias_may_point_at_a_new_tag_from_the_same_batch() -> None:
    curator = ScriptedCurator(
        (
            CurationVerdict("feta", CurationDecision.ALIAS, "ser feta"),
            CurationVerdict("ser feta", CurationDecision.NEW_TAG, None),
        )
    )
    use_case, ingredients = _curation(curator, ("feta", "ser feta"))

    run = use_case.execute(NOW, 100)

    assert run.aliases == ("feta -> ser feta",)
    assert _names(ingredients, IngredientNameKind.CANONICAL) == ["jajka", "ser feta"]


def test_a_candidate_without_a_verdict_stays_pending() -> None:
    use_case, _ = _curation(ScriptedCurator(()), ("mąka ziemniaczana",))

    run = use_case.execute(NOW, 100)

    assert run.skipped == ("mąka ziemniaczana: no verdict",)
