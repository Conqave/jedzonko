from datetime import UTC, datetime

import pytest

from catalog.application.errors import (
    IngredientNotFoundError,
    NotAHouseholdMemberError,
    ProductNotFoundError,
)
from catalog.application.use_cases.confirm_product_ingredient import ConfirmProductIngredient
from catalog.application.use_cases.get_confirmed_product_ingredients import (
    GetConfirmedProductIngredients,
)
from catalog.application.use_cases.propose_product_ingredient import ProposeProductIngredient
from catalog.application.use_cases.reject_product_ingredient import RejectProductIngredient
from catalog.domain.errors import (
    InvalidProductIngredientTransitionError,
    ProductAlreadyClassifiedError,
    ProductIngredientAlreadyRecordedError,
)
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import IngredientNameText
from catalog.domain.product_ingredient import ProductIngredientSource, ProductIngredientStatus
from catalog.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeIngredientRepository,
    FakeProductClassificationRepository,
    FakeTransactionManager,
)

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
ALA = 1
OLA = 2
HOME = 100
OTHER_HOME = 200
EGG_BOX = 10
FOREIGN_PRODUCT = 20


class Catalog:
    def __init__(self) -> None:
        self.transactions = FakeTransactionManager()
        self.ingredients = FakeIngredientRepository()
        self.classifications = FakeProductClassificationRepository(self.transactions)
        self.memberships = FakeHouseholdMembershipReader({(ALA, HOME), (OLA, OTHER_HOME)})
        self.classifications.add_product(EGG_BOX, HOME)
        self.classifications.add_product(FOREIGN_PRODUCT, OTHER_HOME)
        self.eggs = self.ingredients.create(
            IngredientNameText.parse("Jajka"), IngredientNameSource.MANUAL
        ).id
        self.butter = self.ingredients.create(
            IngredientNameText.parse("Masło"), IngredientNameSource.MANUAL
        ).id

    def propose(self) -> ProposeProductIngredient:
        return ProposeProductIngredient(self.classifications, self.ingredients, self.transactions)

    def confirm(self) -> ConfirmProductIngredient:
        return ConfirmProductIngredient(
            self.classifications, self.ingredients, self.memberships, self.transactions
        )

    def reject(self) -> RejectProductIngredient:
        return RejectProductIngredient(self.classifications, self.memberships, self.transactions)

    def confirmed(self, household_id: int) -> dict[int, int]:
        return GetConfirmedProductIngredients(self.classifications).execute(household_id)


@pytest.fixture
def catalog() -> Catalog:
    return Catalog()


def test_a_model_proposal_is_stored_and_does_not_classify_the_product(catalog: Catalog) -> None:
    proposal = catalog.propose().execute(EGG_BOX, catalog.eggs, "gpt-oss:20b", NOW)

    assert proposal.status is ProductIngredientStatus.PROPOSED
    assert catalog.classifications.saved == [proposal]
    assert catalog.confirmed(HOME) == {}


def test_proposing_for_a_missing_product_or_ingredient_fails(catalog: Catalog) -> None:
    with pytest.raises(ProductNotFoundError):
        catalog.propose().execute(404, catalog.eggs, "gpt-oss:20b", NOW)
    with pytest.raises(IngredientNotFoundError):
        catalog.propose().execute(EGG_BOX, 404, "gpt-oss:20b", NOW)


def test_the_model_cannot_override_a_user_decision(catalog: Catalog) -> None:
    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, NOW)

    with pytest.raises(ProductAlreadyClassifiedError):
        catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", LATER)
    assert catalog.confirmed(HOME) == {EGG_BOX: catalog.eggs}


def test_a_rejection_is_remembered_and_blocks_the_same_proposal(catalog: Catalog) -> None:
    catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", NOW)
    catalog.reject().execute(ALA, EGG_BOX, catalog.butter, NOW)

    with pytest.raises(ProductIngredientAlreadyRecordedError):
        catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", LATER)


def test_confirming_a_proposal_classifies_the_product(catalog: Catalog) -> None:
    catalog.propose().execute(EGG_BOX, catalog.eggs, "gpt-oss:20b", NOW)

    confirmed = catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, LATER)

    assert confirmed.status is ProductIngredientStatus.CONFIRMED
    assert confirmed.source is ProductIngredientSource.MODEL
    assert confirmed.decided_at == LATER
    assert catalog.confirmed(HOME) == {EGG_BOX: catalog.eggs}


def test_confirming_another_ingredient_replaces_the_previous_one_atomically(
    catalog: Catalog,
) -> None:
    catalog.confirm().execute(ALA, EGG_BOX, catalog.butter, NOW)
    opened_before = catalog.transactions.opened

    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, LATER)

    assert catalog.transactions.opened == opened_before + 1
    assert catalog.confirmed(HOME) == {EGG_BOX: catalog.eggs}
    classification = catalog.classifications.find(EGG_BOX)
    assert classification is not None
    previous = classification.find(catalog.butter)
    assert previous is not None and previous.status is ProductIngredientStatus.REJECTED


def test_confirming_the_same_ingredient_again_stores_nothing(catalog: Catalog) -> None:
    first = catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, NOW)
    saved_before = list(catalog.classifications.saved)

    again = catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, LATER)

    assert again == first
    assert catalog.classifications.saved == saved_before


def test_a_user_can_reconfirm_what_they_rejected(catalog: Catalog) -> None:
    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, NOW)
    catalog.reject().execute(ALA, EGG_BOX, catalog.eggs, NOW)
    assert catalog.confirmed(HOME) == {}

    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, LATER)

    assert catalog.confirmed(HOME) == {EGG_BOX: catalog.eggs}


def test_rejecting_twice_fails(catalog: Catalog) -> None:
    catalog.propose().execute(EGG_BOX, catalog.eggs, "gpt-oss:20b", NOW)
    catalog.reject().execute(ALA, EGG_BOX, catalog.eggs, NOW)

    with pytest.raises(InvalidProductIngredientTransitionError):
        catalog.reject().execute(ALA, EGG_BOX, catalog.eggs, LATER)


def test_only_members_decide_about_a_product(catalog: Catalog) -> None:
    catalog.propose().execute(FOREIGN_PRODUCT, catalog.eggs, "gpt-oss:20b", NOW)

    with pytest.raises(NotAHouseholdMemberError):
        catalog.confirm().execute(ALA, FOREIGN_PRODUCT, catalog.eggs, NOW)
    with pytest.raises(NotAHouseholdMemberError):
        catalog.reject().execute(ALA, FOREIGN_PRODUCT, catalog.eggs, NOW)
    assert catalog.confirmed(OTHER_HOME) == {}


def test_deciding_about_a_missing_product_or_ingredient_fails(catalog: Catalog) -> None:
    with pytest.raises(ProductNotFoundError):
        catalog.confirm().execute(ALA, 404, catalog.eggs, NOW)
    with pytest.raises(IngredientNotFoundError):
        catalog.confirm().execute(ALA, EGG_BOX, 404, NOW)
    with pytest.raises(ProductNotFoundError):
        catalog.reject().execute(ALA, 404, catalog.eggs, NOW)


def test_confirmed_ingredients_are_listed_per_household(catalog: Catalog) -> None:
    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, NOW)
    catalog.propose().execute(FOREIGN_PRODUCT, catalog.butter, "gpt-oss:20b", NOW)

    assert catalog.confirmed(HOME) == {EGG_BOX: catalog.eggs}
    assert catalog.confirmed(OTHER_HOME) == {}
