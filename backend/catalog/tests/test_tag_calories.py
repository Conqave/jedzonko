from decimal import Decimal

import pytest

from catalog.application.errors import DuplicateCalorieReferenceError, IngredientNotFoundError
from catalog.application.use_cases.import_tag_calories import ImportTagCalories
from catalog.application.use_cases.set_tag_calories import SetTagCalories
from catalog.domain.calories import CalorieReference, CalorieSource, TagCalories
from catalog.domain.errors import InvalidTagCaloriesError
from catalog.domain.ingredient import IngredientNameKind, IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.tests.fakes import FakeIngredientRepository, FakeTransactionManager

SOURCE_URL = "https://example.org/nutrition/apple"


def _tag(repository: FakeIngredientRepository, name: str) -> int:
    catalog_name = CatalogName.parse(name)
    ingredient = repository.create(catalog_name, IngredientNameSource.MANUAL)
    return ingredient.id


def _reference(tag_name: str, kcal: str) -> CalorieReference:
    calories = TagCalories.from_reference(Decimal(kcal), SOURCE_URL)
    return CalorieReference(tag_name=tag_name, calories=calories)


@pytest.fixture
def repository() -> FakeIngredientRepository:
    return FakeIngredientRepository()


@pytest.fixture
def transactions() -> FakeTransactionManager:
    return FakeTransactionManager()


@pytest.mark.parametrize("kcal", ["-0.1", "900.1", "52.25"])
def test_calories_outside_the_range_or_precision_are_rejected(kcal: str) -> None:
    with pytest.raises(InvalidTagCaloriesError):
        TagCalories.manual(Decimal(kcal))


def test_calories_at_the_bounds_are_accepted() -> None:
    assert TagCalories.manual(Decimal("0")).kcal_per_100g == Decimal("0")
    assert TagCalories.manual(Decimal("900.0")).kcal_per_100g == Decimal("900")


def test_only_reference_values_carry_a_source_url() -> None:
    with pytest.raises(InvalidTagCaloriesError):
        TagCalories(kcal_per_100g=Decimal("52"), source=CalorieSource.MANUAL, reference_url="x")
    with pytest.raises(InvalidTagCaloriesError):
        TagCalories(kcal_per_100g=Decimal("52"), source=CalorieSource.REFERENCE, reference_url=None)
    with pytest.raises(InvalidTagCaloriesError):
        TagCalories.from_reference(Decimal("52"), "  ")


def test_an_imported_value_must_come_from_a_reference() -> None:
    manual = TagCalories.manual(Decimal("52"))

    with pytest.raises(InvalidTagCaloriesError):
        CalorieReference(tag_name="jabłko", calories=manual)


def test_a_member_sets_calories_manually(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    apple_id = _tag(repository, "Jabłko")

    ingredient = SetTagCalories(repository, transactions).execute(apple_id, Decimal("52.0"))

    assert ingredient.calories == TagCalories.manual(Decimal("52"))
    assert repository.ingredients[apple_id].calories == TagCalories.manual(Decimal("52"))
    assert transactions.opened == 1


def test_a_manual_value_replaces_a_reference_value(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    apple_id = _tag(repository, "Jabłko")
    reference = TagCalories.from_reference(Decimal("52"), SOURCE_URL)
    repository.save_calories(apple_id, reference)

    SetTagCalories(repository, transactions).execute(apple_id, Decimal("60"))

    assert repository.ingredients[apple_id].calories == TagCalories.manual(Decimal("60"))


def test_clearing_calories_leaves_the_tag_without_them(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    apple_id = _tag(repository, "Jabłko")
    use_case = SetTagCalories(repository, transactions)
    use_case.execute(apple_id, Decimal("52"))

    ingredient = use_case.execute(apple_id, None)

    assert ingredient.calories is None
    assert repository.ingredients[apple_id].calories is None


def test_setting_calories_of_an_unknown_tag_fails(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    with pytest.raises(IngredientNotFoundError):
        SetTagCalories(repository, transactions).execute(404, Decimal("52"))


def test_setting_invalid_calories_fails_before_touching_storage(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    apple_id = _tag(repository, "Jabłko")

    with pytest.raises(InvalidTagCaloriesError):
        SetTagCalories(repository, transactions).execute(apple_id, Decimal("1000"))

    assert repository.ingredients[apple_id].calories is None
    assert transactions.opened == 0


def test_import_fills_tags_by_canonical_name_or_alias(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    apple_id = _tag(repository, "Jabłko")
    egg_id = _tag(repository, "Jajka")
    alias = CatalogName.parse("jajko")
    repository.add_name(egg_id, alias, IngredientNameKind.ALIAS, IngredientNameSource.MANUAL)
    references = (
        _reference("JABŁKO", "52"),
        _reference("jajko", "143"),
        _reference("kawior", "264"),
    )

    run = ImportTagCalories(repository, transactions).execute(references)

    assert run.updated == ("Jabłko", "Jajka")
    assert run.unknown == ("kawior",)
    assert run.unchanged == ()
    assert run.skipped_manual == ()
    assert repository.ingredients[apple_id].calories == references[0].calories
    assert repository.ingredients[egg_id].calories == references[1].calories
    assert transactions.opened == 1


def test_import_never_overwrites_a_manual_value(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    apple_id = _tag(repository, "Jabłko")
    manual = TagCalories.manual(Decimal("60"))
    repository.save_calories(apple_id, manual)

    run = ImportTagCalories(repository, transactions).execute((_reference("jabłko", "52"),))

    assert run.skipped_manual == ("Jabłko",)
    assert run.updated == ()
    assert repository.ingredients[apple_id].calories == manual


def test_a_later_import_refreshes_reference_values(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    apple_id = _tag(repository, "Jabłko")
    use_case = ImportTagCalories(repository, transactions)
    use_case.execute((_reference("jabłko", "52"),))

    same = use_case.execute((_reference("jabłko", "52"),))
    refreshed = use_case.execute((_reference("jabłko", "54.5"),))

    assert same.unchanged == ("Jabłko",)
    assert refreshed.updated == ("Jabłko",)
    assert repository.ingredients[apple_id].calories == _reference("x", "54.5").calories


def test_a_file_naming_one_tag_twice_is_refused(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    egg_id = _tag(repository, "Jajka")
    alias = CatalogName.parse("jajko")
    repository.add_name(egg_id, alias, IngredientNameKind.ALIAS, IngredientNameSource.MANUAL)
    references = (_reference("jajka", "143"), _reference("jajko", "150"))

    with pytest.raises(DuplicateCalorieReferenceError):
        ImportTagCalories(repository, transactions).execute(references)
