from datetime import UTC, datetime

import pytest

from catalog.application.errors import IngredientClassifierUnavailableError
from catalog.application.ports.ingredient_classifier import IngredientClassifier
from catalog.application.use_cases.propose_ingredients_for_products import (
    ProposeIngredientsForProducts,
)
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.domain.product_ingredient import (
    ProductIngredient,
    ProductIngredientSource,
    ProductIngredientStatus,
)
from catalog.tests.fakes import (
    FakeIngredientClassifier,
    FakeIngredientRepository,
    FakeProductClassificationRepository,
    FakeProductRepository,
    FakeTransactionManager,
)

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
HOME = 1


class Setup:
    def __init__(self) -> None:
        self.transactions = FakeTransactionManager()
        self.products = FakeProductRepository()
        self.ingredients = FakeIngredientRepository()
        self.classifications = FakeProductClassificationRepository(self.transactions)
        for name in ["jajka", "masło", "mleko"]:
            self.ingredients.create(CatalogName.parse(name), IngredientNameSource.ANIA_GOTUJE)

    def product(self, name: str) -> int:
        product = self.products.add(HOME, name)
        self.classifications.add_product(product.id, HOME)
        return product.id

    def run(
        self, classifier: IngredientClassifier, question_limit: int = 10, dry_run: bool = False
    ) -> tuple[ProductIngredient, ...]:
        use_case = ProposeIngredientsForProducts(
            self.products,
            self.ingredients,
            self.classifications,
            classifier,
            self.transactions,
            question_limit,
        )
        return use_case.execute(NOW, dry_run).proposals


@pytest.fixture
def setup() -> Setup:
    return Setup()


def test_the_model_answer_is_stored_as_a_proposal_only(setup: Setup) -> None:
    product_id = setup.product("Jajka wiejskie")
    classifier = FakeIngredientClassifier({"Jajka wiejskie": ("jajka",)})

    proposals = setup.run(classifier)

    assert [(each.product_id, each.status, each.source) for each in proposals] == [
        (product_id, ProductIngredientStatus.PROPOSED, ProductIngredientSource.MODEL)
    ]
    assert setup.classifications.list_confirmed(HOME) == {}


def test_the_model_sees_every_tag_and_may_choose_several(setup: Setup) -> None:
    setup.product("Masło extra")
    classifier = FakeIngredientClassifier({"Masło extra": ("masło", "mleko")})

    proposals = setup.run(classifier)

    assert classifier.questions == [("Masło extra", ("jajka", "masło", "mleko"))]
    assert len(proposals) == 2


def test_a_rejected_pair_is_not_offered_again(setup: Setup) -> None:
    product_id = setup.product("Mleko 3,2%")
    milk = setup.ingredients.find_by_normalized_name("mleko")
    assert milk is not None
    rejection = ProductIngredient(
        product_id=product_id,
        ingredient_id=milk.id,
        status=ProductIngredientStatus.REJECTED,
        source=ProductIngredientSource.MANUAL,
        model_name=None,
        proposed_at=None,
        decided_at=NOW,
    )
    with setup.transactions.atomic():
        setup.classifications.save((rejection,))
    classifier = FakeIngredientClassifier({"Mleko 3,2%": ()})

    proposals = setup.run(classifier)

    assert proposals == ()
    assert classifier.questions == [("Mleko 3,2%", ("jajka", "masło"))]


def test_the_question_limit_bounds_a_run(setup: Setup) -> None:
    setup.product("Jajka wiejskie")
    setup.product("Masło extra")
    classifier = FakeIngredientClassifier({"Jajka wiejskie": ("jajka",), "Masło extra": ("masło",)})

    proposals = setup.run(classifier, question_limit=1)

    assert len(proposals) == 1
    assert len(classifier.questions) == 1


def test_a_dry_run_stores_nothing(setup: Setup) -> None:
    setup.product("Jajka wiejskie")
    classifier = FakeIngredientClassifier({"Jajka wiejskie": ("jajka",)})

    proposals = setup.run(classifier, dry_run=True)

    assert len(proposals) == 1
    assert setup.classifications.saved == []


class UnavailableClassifier(FakeIngredientClassifier):
    def find_matching_tags(self, product_name: str, tag_names: tuple[str, ...]) -> tuple[int, ...]:
        raise IngredientClassifierUnavailableError("Ollama is down.")


def test_an_unavailable_model_ends_the_run_with_a_reported_failure(setup: Setup) -> None:
    setup.product("Jajka wiejskie")
    use_case = ProposeIngredientsForProducts(
        setup.products,
        setup.ingredients,
        setup.classifications,
        UnavailableClassifier({}),
        setup.transactions,
        10,
    )

    run = use_case.execute(NOW, dry_run=False)

    assert run.failure == "Ollama is down."
    assert run.proposals == ()
