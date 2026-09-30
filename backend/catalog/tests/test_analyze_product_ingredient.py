from datetime import UTC, datetime

import pytest

from catalog.application.use_cases.analyze_product_ingredient import AnalyzeProductIngredient
from catalog.application.use_cases.delete_rejected_product_ingredients import (
    DeleteRejectedProductIngredients,
)
from catalog.application.use_cases.reject_product_ingredient import RejectProductIngredient
from catalog.domain.ingredient import IngredientNameSource
from catalog.domain.names import CatalogName
from catalog.domain.product_ingredient import ProductIngredientStatus
from catalog.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeIngredientClassifier,
    FakeIngredientRepository,
    FakeProductClassificationRepository,
    FakeProductRepository,
    FakeTransactionManager,
)
from shared.household_membership import NotAHouseholdMemberError

NOW = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
ALA = 5
HOME = 1


class Analysis:
    def __init__(self) -> None:
        self.transactions = FakeTransactionManager()
        self.products = FakeProductRepository()
        self.ingredients = FakeIngredientRepository()
        self.classifications = FakeProductClassificationRepository(self.transactions)
        for name in ["mleko", "mleko zsiadłe", "masło"]:
            self.ingredients.create(CatalogName.parse(name), IngredientNameSource.ANIA_GOTUJE)
        product = self.products.add(HOME, "Mleko 3,2%")
        self.classifications.add_product(product.id, HOME)
        self.product_id = product.id
        self.memberships = FakeHouseholdMembershipReader({(ALA, HOME)})

    def reject(self, name: str) -> None:
        ingredient = self.ingredients.find_by_normalized_name(name)
        assert ingredient is not None
        use_case = RejectProductIngredient(
            self.classifications, self.memberships, self.transactions
        )
        use_case.execute(ALA, self.product_id, ingredient.id, NOW)

    def delete_rejected(self) -> None:
        use_case = DeleteRejectedProductIngredients(
            self.classifications, self.memberships, self.transactions
        )
        use_case.execute(ALA, self.product_id)

    def analyze(self, classifier: FakeIngredientClassifier, user_id: int = ALA) -> bool:
        use_case = AnalyzeProductIngredient(
            self.products,
            self.ingredients,
            self.classifications,
            classifier,
            self.memberships,
            self.transactions,
        )
        return use_case.execute(user_id, self.product_id, NOW) != ()

    def statuses(self) -> dict[str, ProductIngredientStatus]:
        classification = self.classifications.find(self.product_id)
        assert classification is not None
        found = self.ingredients.find_many({link.ingredient_id for link in classification.links})
        return {found[link.ingredient_id].name: link.status for link in classification.links}


@pytest.fixture
def analysis() -> Analysis:
    return Analysis()


def test_the_model_assigns_tags_to_one_product(analysis: Analysis) -> None:
    classifier = FakeIngredientClassifier({"Mleko 3,2%": ("mleko",)})

    assert analysis.analyze(classifier) is True
    assert analysis.statuses() == {"mleko": ProductIngredientStatus.CONFIRMED}


def test_analysing_again_offers_only_ingredients_not_decided_yet(analysis: Analysis) -> None:
    analysis.analyze(FakeIngredientClassifier({"Mleko 3,2%": ("mleko",)}))
    classifier = FakeIngredientClassifier({"Mleko 3,2%": ("mleko zsiadłe",)})

    analysis.analyze(classifier)

    assert classifier.questions == [("Mleko 3,2%", ("masło", "mleko zsiadłe"))]


def test_no_fitting_ingredient_leaves_the_product_as_it_was(analysis: Analysis) -> None:
    assert analysis.analyze(FakeIngredientClassifier({"Mleko 3,2%": ()})) is False
    assert analysis.statuses() == {}


def test_a_tagged_product_is_offered_only_the_other_tags(analysis: Analysis) -> None:
    milk = analysis.ingredients.find_by_normalized_name("mleko")
    assert milk is not None
    classification = analysis.classifications.find(analysis.product_id)
    assert classification is not None
    with analysis.transactions.atomic():
        analysis.classifications.save(classification.confirm(milk.id, NOW))
    classifier = FakeIngredientClassifier({"Mleko 3,2%": ()})

    analysis.analyze(classifier)

    assert classifier.questions == [("Mleko 3,2%", ("masło", "mleko zsiadłe"))]


def test_a_non_member_cannot_analyse(analysis: Analysis) -> None:
    with pytest.raises(NotAHouseholdMemberError):
        analysis.analyze(FakeIngredientClassifier({}), user_id=99)


def test_a_rejected_tag_is_not_offered_again(analysis: Analysis) -> None:
    analysis.analyze(FakeIngredientClassifier({"Mleko 3,2%": ("mleko",)}))
    analysis.reject("mleko")
    classifier = FakeIngredientClassifier({"Mleko 3,2%": ()})

    analysis.analyze(classifier)

    assert classifier.questions == [("Mleko 3,2%", ("masło", "mleko zsiadłe"))]


def test_a_deleted_rejection_may_be_offered_again(analysis: Analysis) -> None:
    analysis.analyze(FakeIngredientClassifier({"Mleko 3,2%": ("mleko",)}))
    analysis.reject("mleko")
    analysis.delete_rejected()
    classifier = FakeIngredientClassifier({"Mleko 3,2%": ("mleko",)})

    analysis.analyze(classifier)

    assert classifier.questions == [("Mleko 3,2%", ("masło", "mleko", "mleko zsiadłe"))]
    assert analysis.statuses() == {"mleko": ProductIngredientStatus.CONFIRMED}
