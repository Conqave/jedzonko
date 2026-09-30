import pytest

from catalog.application.use_cases.add_ingredient_alias import AddIngredientAlias
from catalog.application.use_cases.create_ingredient import CreateIngredient
from catalog.application.use_cases.search_ingredients import (
    SEARCH_RESULT_LIMIT,
    SearchIngredients,
)
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.ingredient_search import NameMatchRank, rank_name_match
from catalog.tests.fakes import FakeIngredientRepository, FakeTransactionManager


@pytest.fixture
def repository() -> FakeIngredientRepository:
    return FakeIngredientRepository()


@pytest.fixture
def transactions() -> FakeTransactionManager:
    return FakeTransactionManager()


def _create(
    repository: FakeIngredientRepository,
    transactions: FakeTransactionManager,
    names: list[str],
) -> None:
    create = CreateIngredient(repository, transactions)
    for name in names:
        create.execute(name, IngredientNameSource.MANUAL)


def _alias(
    repository: FakeIngredientRepository,
    transactions: FakeTransactionManager,
    ingredient_name: str,
    alias: str,
) -> None:
    ingredient = repository.find_by_normalized_name(ingredient_name)
    assert ingredient is not None
    AddIngredientAlias(repository, transactions).execute(
        ingredient.id, alias, IngredientNameSource.ANIA_GOTUJE
    )


def _search(repository: FakeIngredientRepository, query: str) -> list[str]:
    found = SearchIngredients(repository).execute(query)
    return [ingredient.name for ingredient in found]


@pytest.mark.parametrize(
    ("normalized_name", "expected"),
    [
        ("mak", NameMatchRank.EXACT),
        ("mak suchy", NameMatchRank.NAME_PREFIX),
        ("maka", NameMatchRank.NAME_PREFIX),
        ("bialy mak", NameMatchRank.WORD_PREFIX),
        ("skrobia/maka ziemniaczana", NameMatchRank.WORD_PREFIX),
        ("dynia makaronowa", NameMatchRank.WORD_PREFIX),
        ("kajmak", NameMatchRank.CONTAINS),
        ("galaretka o smaku malinowym", NameMatchRank.CONTAINS),
    ],
)
def test_a_name_is_ranked_by_where_the_query_matches(
    normalized_name: str, expected: NameMatchRank
) -> None:
    assert rank_name_match(normalized_name, "mak") is expected


def test_ranking_a_name_without_the_query_is_a_broken_contract() -> None:
    with pytest.raises(AssertionError):
        rank_name_match("ryz", "mak")


def test_the_exact_match_comes_first_then_prefixes_then_words_then_the_rest(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    _create(
        repository,
        transactions,
        ["kajmak", "dynia makaronowa", "galaretka", "mąka", "biały mak", "mak suchy", "mak"],
    )
    _alias(repository, transactions, "galaretka", "galaretka o smaku malinowym")

    found = _search(repository, "mak")

    assert found == [
        "mak",
        "mak suchy",
        "mąka",
        "biały mak",
        "dynia makaronowa",
        "galaretka",
        "kajmak",
    ]


def test_an_alias_match_ranks_its_ingredient_like_its_own_name(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    _create(
        repository,
        transactions,
        ["komosa ryżowa", "makaron orzo", "ryż biały", "ryż", "ryż arborio"],
    )
    _alias(repository, transactions, "makaron orzo", "makaron w kształcie ryżu orzo")
    _alias(repository, transactions, "ryz arborio", "ryż do risotto")
    _alias(repository, transactions, "ryz bialy", "biały ryż")

    found = _search(repository, "RYŻ")

    assert found == ["ryż", "ryż arborio", "ryż biały", "komosa ryżowa", "makaron orzo"]


def test_an_ingredient_takes_the_best_rank_of_its_names(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    _create(repository, transactions, ["arborio", "ryż biały"])
    _alias(repository, transactions, "arborio", "ryż")

    found = _search(repository, "ryz")

    assert found == ["arborio", "ryż biały"]


def test_search_returns_at_most_the_limit(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    names = [f"ryż {number:02d}" for number in range(SEARCH_RESULT_LIMIT + 5)]
    _create(repository, transactions, names)

    found = _search(repository, "ryz")

    assert found == names[:SEARCH_RESULT_LIMIT]


def test_a_blank_query_finds_nothing(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    _create(repository, transactions, ["ryż"])

    assert _search(repository, "   ") == []
