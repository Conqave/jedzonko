from datetime import UTC, datetime

import pytest

from catalog.application.errors import IngredientNotFoundError
from catalog.application.use_cases.merge_ingredients import MergeIngredients
from catalog.domain.errors import IngredientMergeError
from catalog.domain.ingredient import IngredientNameKind, IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.domain.product_ingredient import (
    ProductIngredient,
    ProductIngredientSource,
    ProductIngredientStatus,
)
from catalog.tests.fakes import (
    FakeIngredientLineRepository,
    FakeIngredientReferences,
    FakeIngredientRepository,
    FakeProductClassificationRepository,
    FakeTransactionManager,
)

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


class Setup:
    def __init__(self) -> None:
        self.transactions = FakeTransactionManager()
        self.ingredients = FakeIngredientRepository()
        self.classifications = FakeProductClassificationRepository(self.transactions)
        self.references = FakeIngredientReferences()
        self.jaja = self._ingredient("jaja")
        self.jajka = self._ingredient("jajka")
        self.merge = MergeIngredients(
            self.ingredients,
            self.classifications,
            (self.references,),
            FakeIngredientLineRepository({}),
            self.transactions,
        )

    def _ingredient(self, name: str) -> int:
        text = CatalogName.parse(name)
        return self.ingredients.create(text, IngredientNameSource.ANIA_GOTUJE).id

    def link(self, product_id: int, ingredient_id: int, status: ProductIngredientStatus) -> None:
        if product_id not in self.classifications.products:
            self.classifications.add_product(product_id, household_id=1)
        decided_at = None if status is ProductIngredientStatus.PROPOSED else NOW
        link = ProductIngredient(
            product_id=product_id,
            ingredient_id=ingredient_id,
            status=status,
            source=ProductIngredientSource.MANUAL,
            model_name=None,
            proposed_at=None,
            decided_at=decided_at,
        )
        with self.transactions.atomic():
            self.classifications.save((link,))

    def status_of(self, product_id: int, ingredient_id: int) -> ProductIngredientStatus | None:
        classification = self.classifications.find(product_id)
        assert classification is not None
        link = classification.find(ingredient_id)
        return None if link is None else link.status


@pytest.fixture
def setup() -> Setup:
    return Setup()


def test_the_duplicate_disappears_and_its_names_become_aliases(setup: Setup) -> None:
    target = setup.merge.execute(setup.jaja, setup.jajka)

    assert target.id == setup.jajka
    assert setup.ingredients.find(setup.jaja) is None
    names = {(name.normalized_name, name.kind) for name in setup.ingredients.names}
    assert names == {("jaja", IngredientNameKind.ALIAS), ("jajka", IngredientNameKind.CANONICAL)}


def test_product_links_move_to_the_target(setup: Setup) -> None:
    setup.link(10, setup.jaja, ProductIngredientStatus.CONFIRMED)

    setup.merge.execute(setup.jaja, setup.jajka)

    assert setup.status_of(10, setup.jajka) is ProductIngredientStatus.CONFIRMED
    assert setup.status_of(10, setup.jaja) is None


def test_the_stronger_decision_survives_when_a_product_links_both(setup: Setup) -> None:
    setup.link(10, setup.jaja, ProductIngredientStatus.CONFIRMED)
    setup.link(10, setup.jajka, ProductIngredientStatus.REJECTED)
    setup.link(11, setup.jaja, ProductIngredientStatus.PROPOSED)
    setup.link(11, setup.jajka, ProductIngredientStatus.CONFIRMED)

    setup.merge.execute(setup.jaja, setup.jajka)

    assert setup.status_of(10, setup.jajka) is ProductIngredientStatus.CONFIRMED
    assert setup.status_of(11, setup.jajka) is ProductIngredientStatus.CONFIRMED


def test_other_features_are_told_to_move_their_rows(setup: Setup) -> None:
    setup.merge.execute(setup.jaja, setup.jajka)

    assert setup.references.reassigned == [(setup.jaja, setup.jajka)]


def test_the_merge_is_one_transaction(setup: Setup) -> None:
    setup.merge.execute(setup.jaja, setup.jajka)

    assert setup.transactions.opened == 1


def test_an_ingredient_is_not_merged_into_itself(setup: Setup) -> None:
    with pytest.raises(IngredientMergeError):
        setup.merge.execute(setup.jaja, setup.jaja)


def test_both_ingredients_must_exist(setup: Setup) -> None:
    with pytest.raises(IngredientNotFoundError):
        setup.merge.execute(404, setup.jajka)
    with pytest.raises(IngredientNotFoundError):
        setup.merge.execute(setup.jaja, 404)
