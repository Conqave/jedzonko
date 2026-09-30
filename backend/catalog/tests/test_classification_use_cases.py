from datetime import UTC, datetime

import pytest

from catalog.application.errors import (
    IngredientNotFoundError,
    ProductNotFoundError,
)
from catalog.application.use_cases.confirm_product_ingredient import ConfirmProductIngredient
from catalog.application.use_cases.delete_product_ingredient import DeleteProductIngredient
from catalog.application.use_cases.delete_rejected_product_ingredients import (
    DeleteRejectedProductIngredients,
)
from catalog.application.use_cases.propose_product_ingredient import ProposeProductIngredient
from catalog.application.use_cases.reject_product_ingredient import RejectProductIngredient
from catalog.domain.errors import (
    ConfirmedProductIngredientDeletionError,
    InvalidProductIngredientTransitionError,
    ProductIngredientAlreadyRecordedError,
    ProductIngredientNotFoundError,
)
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.domain.product_ingredient import ProductIngredientSource, ProductIngredientStatus
from catalog.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeIngredientRepository,
    FakeProductClassificationRepository,
    FakeTransactionManager,
)
from shared.household_membership import NotAHouseholdMemberError

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
            CatalogName.parse("Jajka"), IngredientNameSource.MANUAL
        ).id
        self.butter = self.ingredients.create(
            CatalogName.parse("Masło"), IngredientNameSource.MANUAL
        ).id

    def propose(self) -> ProposeProductIngredient:
        return ProposeProductIngredient(self.classifications, self.ingredients, self.transactions)

    def confirm(self) -> ConfirmProductIngredient:
        return ConfirmProductIngredient(
            self.classifications, self.ingredients, self.memberships, self.transactions
        )

    def reject(self) -> RejectProductIngredient:
        return RejectProductIngredient(self.classifications, self.memberships, self.transactions)

    def delete(self) -> DeleteProductIngredient:
        return DeleteProductIngredient(self.classifications, self.memberships, self.transactions)

    def delete_rejected(self) -> DeleteRejectedProductIngredients:
        return DeleteRejectedProductIngredients(
            self.classifications, self.memberships, self.transactions
        )

    def linked(self, product_id: int) -> dict[int, ProductIngredientStatus]:
        classification = self.classifications.find(product_id)
        assert classification is not None
        return {link.ingredient_id: link.status for link in classification.links}

    def confirmed(self, household_id: int) -> dict[int, tuple[int, ...]]:
        return self.classifications.list_confirmed(household_id)


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


def test_a_model_proposal_never_changes_a_confirmed_tag(catalog: Catalog) -> None:
    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, NOW)

    catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", LATER)

    assert catalog.confirmed(HOME) == {EGG_BOX: (catalog.eggs,)}


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
    assert catalog.confirmed(HOME) == {EGG_BOX: (catalog.eggs,)}


def test_confirming_another_tag_adds_it(catalog: Catalog) -> None:
    catalog.confirm().execute(ALA, EGG_BOX, catalog.butter, NOW)

    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, LATER)

    assert set(catalog.confirmed(HOME)[EGG_BOX]) == {catalog.butter, catalog.eggs}


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

    assert catalog.confirmed(HOME) == {EGG_BOX: (catalog.eggs,)}


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

    assert catalog.confirmed(HOME) == {EGG_BOX: (catalog.eggs,)}
    assert catalog.confirmed(OTHER_HOME) == {}


def test_deleting_a_rejection_forgets_it_so_it_may_be_proposed_again(catalog: Catalog) -> None:
    catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", NOW)
    catalog.reject().execute(ALA, EGG_BOX, catalog.butter, NOW)

    catalog.delete().execute(ALA, EGG_BOX, catalog.butter)
    proposal = catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", LATER)

    assert proposal.status is ProductIngredientStatus.PROPOSED
    assert catalog.linked(EGG_BOX) == {catalog.butter: ProductIngredientStatus.PROPOSED}


def test_a_pending_proposal_can_be_deleted(catalog: Catalog) -> None:
    catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", NOW)

    catalog.delete().execute(ALA, EGG_BOX, catalog.butter)

    assert catalog.linked(EGG_BOX) == {}


def test_a_confirmed_tag_is_rejected_not_deleted(catalog: Catalog) -> None:
    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, NOW)

    with pytest.raises(ConfirmedProductIngredientDeletionError):
        catalog.delete().execute(ALA, EGG_BOX, catalog.eggs)
    assert catalog.confirmed(HOME) == {EGG_BOX: (catalog.eggs,)}


def test_deleting_an_unrecorded_ingredient_or_missing_product_fails(catalog: Catalog) -> None:
    with pytest.raises(ProductIngredientNotFoundError):
        catalog.delete().execute(ALA, EGG_BOX, catalog.eggs)
    with pytest.raises(ProductNotFoundError):
        catalog.delete().execute(ALA, 404, catalog.eggs)
    with pytest.raises(ProductNotFoundError):
        catalog.delete_rejected().execute(ALA, 404)


def test_deleting_all_rejections_keeps_tags_and_pending_proposals(catalog: Catalog) -> None:
    extra = catalog.ingredients.create(CatalogName.parse("Mleko"), IngredientNameSource.MANUAL).id
    catalog.confirm().execute(ALA, EGG_BOX, catalog.eggs, NOW)
    catalog.propose().execute(EGG_BOX, catalog.butter, "gpt-oss:20b", NOW)
    catalog.confirm().execute(ALA, EGG_BOX, extra, NOW)
    catalog.reject().execute(ALA, EGG_BOX, extra, LATER)

    catalog.delete_rejected().execute(ALA, EGG_BOX)

    assert catalog.linked(EGG_BOX) == {
        catalog.eggs: ProductIngredientStatus.CONFIRMED,
        catalog.butter: ProductIngredientStatus.PROPOSED,
    }


def test_only_members_delete_a_products_links(catalog: Catalog) -> None:
    catalog.propose().execute(FOREIGN_PRODUCT, catalog.eggs, "gpt-oss:20b", NOW)
    catalog.reject().execute(OLA, FOREIGN_PRODUCT, catalog.eggs, NOW)

    with pytest.raises(NotAHouseholdMemberError):
        catalog.delete().execute(ALA, FOREIGN_PRODUCT, catalog.eggs)
    with pytest.raises(NotAHouseholdMemberError):
        catalog.delete_rejected().execute(ALA, FOREIGN_PRODUCT)
    assert catalog.linked(FOREIGN_PRODUCT) == {catalog.eggs: ProductIngredientStatus.REJECTED}
