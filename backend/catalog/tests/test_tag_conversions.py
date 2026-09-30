from decimal import Decimal

import pytest

from catalog.application.errors import DuplicateTagReferenceError, IngredientNotFoundError
from catalog.application.reference_import import ImportedFact, TagFact
from catalog.application.use_cases.import_tag_conversions import ImportTagConversions
from catalog.application.use_cases.set_tag_density import SetTagDensity
from catalog.application.use_cases.set_tag_piece_weight import SetTagPieceWeight
from catalog.domain.conversions import ConversionReference, Density, PieceWeight
from catalog.domain.errors import (
    InvalidConversionReferenceError,
    InvalidDensityError,
    InvalidPieceWeightError,
)
from catalog.domain.ingredient import IngredientNameKind, IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.domain.provenance import (
    Provenance,
    ReferenceImportDecision,
    decide_reference_import,
)
from catalog.tests.fakes import FakeIngredientRepository, FakeTransactionManager

SOURCE_URL = "https://example.org/nutrition/egg"


def _tag(repository: FakeIngredientRepository, name: str) -> int:
    catalog_name = CatalogName.parse(name)
    ingredient = repository.create(catalog_name, IngredientNameSource.MANUAL)
    return ingredient.id


def _reference(tag_name: str, piece: str | None, density: str | None) -> ConversionReference:
    piece_weight = None if piece is None else PieceWeight.from_reference(Decimal(piece), SOURCE_URL)
    grams_per_ml = None if density is None else Density.from_reference(Decimal(density), SOURCE_URL)
    return ConversionReference(tag_name=tag_name, piece_weight=piece_weight, density=grams_per_ml)


@pytest.fixture
def repository() -> FakeIngredientRepository:
    return FakeIngredientRepository()


@pytest.fixture
def transactions() -> FakeTransactionManager:
    return FakeTransactionManager()


@pytest.mark.parametrize("grams", ["0", "-5", "10000.1", "55.25"])
def test_an_impossible_piece_weight_is_rejected(grams: str) -> None:
    with pytest.raises(InvalidPieceWeightError):
        PieceWeight.manual(Decimal(grams))


@pytest.mark.parametrize("grams_per_ml", ["0", "-1", "3.001", "1.0305"])
def test_an_impossible_density_is_rejected(grams_per_ml: str) -> None:
    with pytest.raises(InvalidDensityError):
        Density.manual(Decimal(grams_per_ml))


def test_conversions_at_the_bounds_are_accepted() -> None:
    assert PieceWeight.manual(Decimal("0.1")).grams_per_piece == Decimal("0.1")
    assert PieceWeight.manual(Decimal("10000")).grams_per_piece == Decimal("10000")
    assert Density.manual(Decimal("0.001")).grams_per_ml == Decimal("0.001")
    assert Density.manual(Decimal("3.000")).grams_per_ml == Decimal("3")


def test_a_conversion_reference_provides_at_least_one_referenced_value() -> None:
    manual = PieceWeight.manual(Decimal("55"))

    with pytest.raises(InvalidConversionReferenceError):
        ConversionReference(tag_name="jajka", piece_weight=None, density=None)
    with pytest.raises(InvalidConversionReferenceError):
        ConversionReference(tag_name="jajka", piece_weight=manual, density=None)


def test_a_manual_value_is_never_replaced_by_a_reference() -> None:
    manual = Provenance.manual()
    reference = Provenance.from_reference(SOURCE_URL)

    assert decide_reference_import(manual, False) is ReferenceImportDecision.KEEP_MANUAL
    assert decide_reference_import(manual, True) is ReferenceImportDecision.KEEP_MANUAL
    assert decide_reference_import(reference, True) is ReferenceImportDecision.UNCHANGED
    assert decide_reference_import(reference, False) is ReferenceImportDecision.UPDATE
    assert decide_reference_import(None, False) is ReferenceImportDecision.UPDATE


def test_a_member_sets_and_clears_the_piece_weight(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    egg_id = _tag(repository, "Jajka")
    use_case = SetTagPieceWeight(repository, transactions)

    saved = use_case.execute(egg_id, Decimal("55.0"))
    stored = repository.ingredients[egg_id].piece_weight
    cleared = use_case.execute(egg_id, None)

    assert saved.piece_weight == PieceWeight.manual(Decimal("55"))
    assert stored == PieceWeight.manual(Decimal("55"))
    assert cleared.piece_weight is None
    assert repository.ingredients[egg_id].piece_weight is None
    assert transactions.opened == 2


def test_a_member_sets_and_clears_the_density(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    milk_id = _tag(repository, "Mleko")
    use_case = SetTagDensity(repository, transactions)

    saved = use_case.execute(milk_id, Decimal("1.03"))
    stored = repository.ingredients[milk_id].density
    cleared = use_case.execute(milk_id, None)

    assert saved.density == Density.manual(Decimal("1.03"))
    assert stored == Density.manual(Decimal("1.03"))
    assert cleared.density is None
    assert repository.ingredients[milk_id].density is None


def test_setting_a_conversion_of_an_unknown_tag_fails(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    with pytest.raises(IngredientNotFoundError):
        SetTagPieceWeight(repository, transactions).execute(404, Decimal("55"))
    with pytest.raises(IngredientNotFoundError):
        SetTagDensity(repository, transactions).execute(404, Decimal("1"))


def test_setting_an_invalid_conversion_fails_before_touching_storage(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    egg_id = _tag(repository, "Jajka")

    with pytest.raises(InvalidPieceWeightError):
        SetTagPieceWeight(repository, transactions).execute(egg_id, Decimal("0"))
    with pytest.raises(InvalidDensityError):
        SetTagDensity(repository, transactions).execute(egg_id, Decimal("5"))

    assert repository.ingredients[egg_id].piece_weight is None
    assert repository.ingredients[egg_id].density is None
    assert transactions.opened == 0


def test_import_fills_only_the_provided_conversions(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    egg_id = _tag(repository, "Jajka")
    milk_id = _tag(repository, "Mleko")
    alias = CatalogName.parse("jajko")
    repository.add_name(egg_id, alias, IngredientNameKind.ALIAS, IngredientNameSource.MANUAL)
    references = (
        _reference("jajko", "55", None),
        _reference("MLEKO", None, "1.03"),
        _reference("kawior", "0.1", None),
    )

    run = ImportTagConversions(repository, transactions).execute(references)

    assert run.updated == (
        ImportedFact(tag_name="Jajka", fact=TagFact.PIECE_WEIGHT),
        ImportedFact(tag_name="Mleko", fact=TagFact.DENSITY),
    )
    assert run.unknown == ("kawior",)
    assert repository.ingredients[egg_id].piece_weight == references[0].piece_weight
    assert repository.ingredients[egg_id].density is None
    assert repository.ingredients[milk_id].piece_weight is None
    assert repository.ingredients[milk_id].density == references[1].density
    assert transactions.opened == 1


def test_import_keeps_a_manual_value_and_still_fills_the_other_conversion(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    egg_id = _tag(repository, "Jajka")
    manual = PieceWeight.manual(Decimal("60"))
    repository.save_piece_weight(egg_id, manual)
    reference = _reference("jajka", "55", "1.03")

    run = ImportTagConversions(repository, transactions).execute((reference,))

    assert run.skipped_manual == (ImportedFact(tag_name="Jajka", fact=TagFact.PIECE_WEIGHT),)
    assert run.updated == (ImportedFact(tag_name="Jajka", fact=TagFact.DENSITY),)
    assert repository.ingredients[egg_id].piece_weight == manual
    assert repository.ingredients[egg_id].density == reference.density


def test_a_later_import_refreshes_reference_conversions(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    egg_id = _tag(repository, "Jajka")
    use_case = ImportTagConversions(repository, transactions)
    use_case.execute((_reference("jajka", "55", None),))

    same = use_case.execute((_reference("jajka", "55", None),))
    refreshed = use_case.execute((_reference("jajka", "58", None),))

    assert same.unchanged == (ImportedFact(tag_name="Jajka", fact=TagFact.PIECE_WEIGHT),)
    assert refreshed.updated == (ImportedFact(tag_name="Jajka", fact=TagFact.PIECE_WEIGHT),)
    assert repository.ingredients[egg_id].piece_weight == _reference("x", "58", None).piece_weight


def test_a_conversion_file_naming_one_tag_twice_is_refused(
    repository: FakeIngredientRepository, transactions: FakeTransactionManager
) -> None:
    egg_id = _tag(repository, "Jajka")
    alias = CatalogName.parse("jajko")
    repository.add_name(egg_id, alias, IngredientNameKind.ALIAS, IngredientNameSource.MANUAL)
    references = (_reference("jajka", "55", None), _reference("jajko", None, "1.03"))

    with pytest.raises(DuplicateTagReferenceError):
        ImportTagConversions(repository, transactions).execute(references)
