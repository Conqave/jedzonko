from decimal import Decimal

import pytest

from recipes.application.errors import InvalidServingsError, RecipeNotFoundError
from recipes.application.use_cases.confirm_recipe_preparation import ConfirmRecipePreparation
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.domain.stock import StockedProduct
from recipes.tests.factories import EGGS, FLOUR, GRAM, make_requirement, make_stock
from recipes.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeInventoryConsumer,
    FakeRecipeRepository,
    FakeStockReader,
    FakeTransactionManager,
)
from shared.household_membership import NotAHouseholdMemberError
from shared.measurement import Quantity


def _recipe(servings: int) -> RecipeDetail:
    summary = RecipeSummary(
        id=1,
        name="omlet",
        description="",
        servings=servings,
        preparation_time_minutes=5,
        cooking_time_minutes=5,
        difficulty=RecipeDifficulty.EASY,
        category=None,
        tag_names=(),
        image_url=None,
        author_username="ala",
    )
    return RecipeDetail(summary=summary, steps=(), ingredients=())


def _build(
    repository: FakeRecipeRepository,
    inventory: list[StockedProduct],
    consumer: FakeInventoryConsumer,
    transaction_manager: FakeTransactionManager,
) -> ConfirmRecipePreparation:
    return ConfirmRecipePreparation(
        repository,
        FakeStockReader(inventory),
        consumer,
        transaction_manager,
        FakeHouseholdMembershipReader({7}),
    )


def test_each_stocked_ingredient_is_consumed_exactly_once() -> None:
    repository = FakeRecipeRepository(
        [_recipe(2)],
        {
            1: [
                make_requirement("jajko", "2", GRAM, EGGS),
                make_requirement("maka", "50", GRAM, FLOUR),
            ]
        },
    )
    consumer = FakeInventoryConsumer()
    transaction_manager = FakeTransactionManager()
    use_case = _build(
        repository,
        [make_stock(1, "jajko", "10", GRAM, EGGS), make_stock(2, "maka", "500", GRAM, FLOUR)],
        consumer,
        transaction_manager,
    )

    use_case.execute(5, 7, 1, 4)

    assert consumer.consumed == [
        (7, 1, Quantity(amount=Decimal("4"), unit=GRAM)),
        (7, 2, Quantity(amount=Decimal("100"), unit=GRAM)),
    ]
    assert transaction_manager.entered_count == 1


def test_ingredients_absent_from_inventory_are_skipped() -> None:
    repository = FakeRecipeRepository(
        [_recipe(2)],
        {
            1: [
                make_requirement("jajko", "2", GRAM, EGGS),
                make_requirement("maka", "50", GRAM, FLOUR),
            ]
        },
    )
    consumer = FakeInventoryConsumer()
    use_case = _build(
        repository, [make_stock(1, "jajko", "10", GRAM, EGGS)], consumer, FakeTransactionManager()
    )

    use_case.execute(5, 7, 1, 2)

    assert [entry[1] for entry in consumer.consumed] == [1]


def test_repeated_confirmation_consumes_again() -> None:
    repository = FakeRecipeRepository(
        [_recipe(2)], {1: [make_requirement("jajko", "2", GRAM, EGGS)]}
    )
    consumer = FakeInventoryConsumer()
    transaction_manager = FakeTransactionManager()
    use_case = _build(
        repository, [make_stock(1, "jajko", "10", GRAM, EGGS)], consumer, transaction_manager
    )

    use_case.execute(5, 7, 1, 2)
    use_case.execute(5, 7, 1, 2)

    assert len(consumer.consumed) == 2
    assert transaction_manager.entered_count == 2


def test_non_member_consumes_nothing() -> None:
    repository = FakeRecipeRepository(
        [_recipe(2)], {1: [make_requirement("jajko", "2", GRAM, EGGS)]}
    )
    consumer = FakeInventoryConsumer()
    transaction_manager = FakeTransactionManager()
    use_case = _build(
        repository, [make_stock(1, "jajko", "10", GRAM, EGGS)], consumer, transaction_manager
    )

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(5, 99, 1, 2)

    assert consumer.consumed == []
    assert transaction_manager.entered_count == 0


def test_zero_servings_is_rejected() -> None:
    consumer = FakeInventoryConsumer()
    use_case = _build(
        FakeRecipeRepository([_recipe(2)], {}), [], consumer, FakeTransactionManager()
    )

    with pytest.raises(InvalidServingsError):
        use_case.execute(5, 7, 1, 0)

    assert consumer.consumed == []


def test_unknown_recipe_is_rejected() -> None:
    consumer = FakeInventoryConsumer()
    use_case = _build(FakeRecipeRepository([], {}), [], consumer, FakeTransactionManager())

    with pytest.raises(RecipeNotFoundError):
        use_case.execute(5, 7, 404, 2)

    assert consumer.consumed == []
