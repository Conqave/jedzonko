import pytest

from catalog.application.errors import DuplicateIngredientNameError, IngredientNotFoundError
from catalog.application.use_cases.add_ingredient_alias import AddIngredientAlias
from catalog.application.use_cases.create_ingredient import CreateIngredient
from catalog.application.use_cases.find_ingredient_by_name import FindIngredientByName
from catalog.domain.errors import InvalidIngredientNameError
from catalog.domain.ingredient import IngredientName, IngredientNameKind, IngredientNameSource
from catalog.tests.fakes import FakeIngredientRepository, FakeTransactionManager


@pytest.fixture
def repository() -> FakeIngredientRepository:
    return FakeIngredientRepository()


@pytest.fixture
def transactions() -> FakeTransactionManager:
    return FakeTransactionManager()


def test_creating_an_ingredient_records_its_canonical_name(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    ingredient = CreateIngredient(repository, transactions).execute(
        " Jajka ", IngredientNameSource.MANUAL
    )

    assert ingredient.name == "Jajka"
    assert repository.names == [
        IngredientName(
            ingredient_id=ingredient.id,
            name="Jajka",
            normalized_name="jajka",
            kind=IngredientNameKind.CANONICAL,
            source=IngredientNameSource.MANUAL,
        )
    ]
    assert transactions.opened == 1


def test_an_ingredient_name_that_normalizes_to_an_existing_one_is_a_duplicate(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    create = CreateIngredient(repository, transactions)
    create.execute("Łosoś", IngredientNameSource.MANUAL)

    with pytest.raises(DuplicateIngredientNameError):
        create.execute("losos", IngredientNameSource.ANIA_GOTUJE)


def test_an_empty_ingredient_name_is_rejected_before_touching_storage(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    with pytest.raises(InvalidIngredientNameError):
        CreateIngredient(repository, transactions).execute("  ", IngredientNameSource.MANUAL)

    assert transactions.opened == 0


def test_an_alias_resolves_to_its_ingredient(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    eggs = CreateIngredient(repository, transactions).execute("Jajka", IngredientNameSource.MANUAL)

    alias = AddIngredientAlias(repository, transactions).execute(
        eggs.id, "jajko", IngredientNameSource.ANIA_GOTUJE
    )

    assert alias.kind is IngredientNameKind.ALIAS
    assert FindIngredientByName(repository).execute("Jajko") == eggs


def test_a_name_belongs_to_one_ingredient_only(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    create = CreateIngredient(repository, transactions)
    eggs = create.execute("Jajka", IngredientNameSource.MANUAL)
    create.execute("Jaja", IngredientNameSource.ANIA_GOTUJE)

    with pytest.raises(DuplicateIngredientNameError):
        AddIngredientAlias(repository, transactions).execute(
            eggs.id, "jaja", IngredientNameSource.MANUAL
        )


def test_an_alias_needs_an_existing_ingredient(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    with pytest.raises(IngredientNotFoundError):
        AddIngredientAlias(repository, transactions).execute(
            404, "jajko", IngredientNameSource.MANUAL
        )


@pytest.mark.parametrize("query", ["jajka", "JAJKA", "  Jajka  "])
def test_finding_by_name_matches_after_normalization(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager, query: str
) -> None:
    eggs = CreateIngredient(repository, transactions).execute("Jajka", IngredientNameSource.MANUAL)

    assert FindIngredientByName(repository).execute(query) == eggs


@pytest.mark.parametrize("query", ["jajk", "jajka wiejskie", "wiejskie jajka", "jajko"])
def test_finding_by_name_never_guesses(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager, query: str
) -> None:
    CreateIngredient(repository, transactions).execute("Jajka", IngredientNameSource.MANUAL)

    assert FindIngredientByName(repository).execute(query) is None


def test_finding_an_empty_name_finds_nothing(repository: FakeIngredientRepository) -> None:
    assert FindIngredientByName(repository).execute("   ") is None
