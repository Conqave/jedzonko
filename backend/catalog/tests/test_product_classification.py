from datetime import UTC, datetime

import pytest

from catalog.domain.classification import ProductClassification
from catalog.domain.errors import (
    InvalidProductClassificationError,
    InvalidProductIngredientError,
    InvalidProductIngredientTransitionError,
    ProductAlreadyClassifiedError,
    ProductIngredientAlreadyRecordedError,
    ProductIngredientNotFoundError,
)
from catalog.domain.product_ingredient import (
    ProductIngredient,
    ProductIngredientSource,
    ProductIngredientStatus,
)

EARLIER = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
PRODUCT = 10
EGGS = 1
BUTTER = 2
MILK = 3


def proposed(ingredient_id: int) -> ProductIngredient:
    return ProductIngredient(
        product_id=PRODUCT,
        ingredient_id=ingredient_id,
        status=ProductIngredientStatus.PROPOSED,
        source=ProductIngredientSource.MODEL,
        model_name="gpt-oss:20b",
        proposed_at=EARLIER,
        decided_at=None,
    )


def decided(ingredient_id: int, status: ProductIngredientStatus) -> ProductIngredient:
    return ProductIngredient(
        product_id=PRODUCT,
        ingredient_id=ingredient_id,
        status=status,
        source=ProductIngredientSource.MANUAL,
        model_name=None,
        proposed_at=None,
        decided_at=EARLIER,
    )


def classification(*links: ProductIngredient) -> ProductClassification:
    return ProductClassification(product_id=PRODUCT, household_id=7, links=links)


# ProductIngredient


def test_a_model_proposal_needs_the_model_name() -> None:
    with pytest.raises(InvalidProductIngredientError):
        ProductIngredient(
            product_id=PRODUCT,
            ingredient_id=EGGS,
            status=ProductIngredientStatus.PROPOSED,
            source=ProductIngredientSource.MODEL,
            model_name=None,
            proposed_at=EARLIER,
            decided_at=None,
        )


def test_only_a_model_proposal_carries_a_model_name() -> None:
    with pytest.raises(InvalidProductIngredientError):
        ProductIngredient(
            product_id=PRODUCT,
            ingredient_id=EGGS,
            status=ProductIngredientStatus.CONFIRMED,
            source=ProductIngredientSource.MANUAL,
            model_name="gpt-oss:20b",
            proposed_at=None,
            decided_at=NOW,
        )


def test_a_pending_proposal_has_no_decision_time() -> None:
    with pytest.raises(InvalidProductIngredientError):
        ProductIngredient(
            product_id=PRODUCT,
            ingredient_id=EGGS,
            status=ProductIngredientStatus.PROPOSED,
            source=ProductIngredientSource.MODEL,
            model_name="gpt-oss:20b",
            proposed_at=EARLIER,
            decided_at=NOW,
        )


@pytest.mark.parametrize(
    "status", [ProductIngredientStatus.CONFIRMED, ProductIngredientStatus.REJECTED]
)
def test_a_decision_has_a_decision_time(status: ProductIngredientStatus) -> None:
    with pytest.raises(InvalidProductIngredientError):
        ProductIngredient(
            product_id=PRODUCT,
            ingredient_id=EGGS,
            status=status,
            source=ProductIngredientSource.MANUAL,
            model_name=None,
            proposed_at=None,
            decided_at=None,
        )


# ProductClassification invariants


def test_a_product_cannot_have_two_confirmed_ingredients() -> None:
    with pytest.raises(InvalidProductClassificationError):
        classification(
            decided(EGGS, ProductIngredientStatus.CONFIRMED),
            decided(BUTTER, ProductIngredientStatus.CONFIRMED),
        )


def test_an_ingredient_is_recorded_once_per_product() -> None:
    with pytest.raises(InvalidProductClassificationError):
        classification(proposed(EGGS), decided(EGGS, ProductIngredientStatus.REJECTED))


def test_links_of_another_product_are_rejected() -> None:
    foreign = ProductIngredient(
        product_id=PRODUCT + 1,
        ingredient_id=EGGS,
        status=ProductIngredientStatus.PROPOSED,
        source=ProductIngredientSource.MODEL,
        model_name="gpt-oss:20b",
        proposed_at=EARLIER,
        decided_at=None,
    )

    with pytest.raises(InvalidProductClassificationError):
        classification(foreign)


# propose


def test_proposing_for_an_unclassified_product_records_a_model_proposal() -> None:
    proposal = classification().propose(EGGS, "gpt-oss:20b", NOW)

    assert proposal == ProductIngredient(
        product_id=PRODUCT,
        ingredient_id=EGGS,
        status=ProductIngredientStatus.PROPOSED,
        source=ProductIngredientSource.MODEL,
        model_name="gpt-oss:20b",
        proposed_at=NOW,
        decided_at=None,
    )


def test_proposing_alongside_other_open_proposals_is_allowed() -> None:
    proposal = classification(proposed(BUTTER)).propose(EGGS, "gpt-oss:20b", NOW)

    assert proposal.ingredient_id == EGGS


def test_a_confirmed_product_receives_no_proposals() -> None:
    with pytest.raises(ProductAlreadyClassifiedError):
        classification(decided(BUTTER, ProductIngredientStatus.CONFIRMED)).propose(
            EGGS, "gpt-oss:20b", NOW
        )


def test_a_rejected_pair_is_never_proposed_again() -> None:
    with pytest.raises(ProductIngredientAlreadyRecordedError):
        classification(decided(EGGS, ProductIngredientStatus.REJECTED)).propose(
            EGGS, "gpt-oss:20b", NOW
        )


def test_an_open_proposal_is_not_proposed_twice() -> None:
    with pytest.raises(ProductIngredientAlreadyRecordedError):
        classification(proposed(EGGS)).propose(EGGS, "gpt-oss:20b", NOW)


# confirm


def test_confirming_a_new_pair_records_a_manual_decision() -> None:
    changes = classification().confirm(EGGS, NOW)

    assert changes == (
        ProductIngredient(
            product_id=PRODUCT,
            ingredient_id=EGGS,
            status=ProductIngredientStatus.CONFIRMED,
            source=ProductIngredientSource.MANUAL,
            model_name=None,
            proposed_at=None,
            decided_at=NOW,
        ),
    )


def test_confirming_a_proposal_keeps_its_provenance() -> None:
    changes = classification(proposed(EGGS)).confirm(EGGS, NOW)

    assert len(changes) == 1
    confirmed = changes[0]
    assert confirmed.status is ProductIngredientStatus.CONFIRMED
    assert confirmed.source is ProductIngredientSource.MODEL
    assert confirmed.model_name == "gpt-oss:20b"
    assert confirmed.proposed_at == EARLIER
    assert confirmed.decided_at == NOW


def test_a_user_may_confirm_a_previously_rejected_pair() -> None:
    changes = classification(decided(EGGS, ProductIngredientStatus.REJECTED)).confirm(EGGS, NOW)

    assert [(change.ingredient_id, change.status) for change in changes] == [
        (EGGS, ProductIngredientStatus.CONFIRMED)
    ]


def test_confirming_another_ingredient_rejects_the_previous_one_first() -> None:
    changes = classification(
        decided(BUTTER, ProductIngredientStatus.CONFIRMED), proposed(EGGS)
    ).confirm(EGGS, NOW)

    assert [(change.ingredient_id, change.status, change.decided_at) for change in changes] == [
        (BUTTER, ProductIngredientStatus.REJECTED, NOW),
        (EGGS, ProductIngredientStatus.CONFIRMED, NOW),
    ]


def test_confirming_the_confirmed_ingredient_again_changes_nothing() -> None:
    assert classification(decided(EGGS, ProductIngredientStatus.CONFIRMED)).confirm(EGGS, NOW) == ()


def test_confirming_leaves_unrelated_proposals_open() -> None:
    before = classification(proposed(BUTTER), proposed(MILK))

    after = before.apply(before.confirm(EGGS, NOW))

    assert after.find(BUTTER) == proposed(BUTTER)
    assert after.find(MILK) == proposed(MILK)
    confirmed = after.confirmed()
    assert confirmed is not None and confirmed.ingredient_id == EGGS


# reject


def test_rejecting_a_proposal_keeps_it_as_a_remembered_rejection() -> None:
    rejection = classification(proposed(EGGS)).reject(EGGS, NOW)

    assert rejection.status is ProductIngredientStatus.REJECTED
    assert rejection.source is ProductIngredientSource.MODEL
    assert rejection.proposed_at == EARLIER
    assert rejection.decided_at == NOW


def test_rejecting_the_confirmed_ingredient_leaves_the_product_unclassified() -> None:
    before = classification(decided(EGGS, ProductIngredientStatus.CONFIRMED))

    after = before.apply((before.reject(EGGS, NOW),))

    assert after.confirmed() is None


def test_rejecting_twice_is_an_invalid_transition() -> None:
    with pytest.raises(InvalidProductIngredientTransitionError):
        classification(decided(EGGS, ProductIngredientStatus.REJECTED)).reject(EGGS, NOW)


def test_rejecting_an_unknown_pair_fails() -> None:
    with pytest.raises(ProductIngredientNotFoundError):
        classification().reject(EGGS, NOW)


def test_after_rejecting_the_confirmed_ingredient_the_model_may_propose_others() -> None:
    before = classification(decided(EGGS, ProductIngredientStatus.CONFIRMED))
    after = before.apply((before.reject(EGGS, NOW),))

    assert after.propose(BUTTER, "gpt-oss:20b", NOW).ingredient_id == BUTTER
    with pytest.raises(ProductIngredientAlreadyRecordedError):
        after.propose(EGGS, "gpt-oss:20b", NOW)
