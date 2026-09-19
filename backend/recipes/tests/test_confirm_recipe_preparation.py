from decimal import Decimal

import pytest

from households.application.access import HouseholdAccessPolicy
from households.application.errors import NotAHouseholdMemberError
from inventory.domain.models import InventoryItemSnapshot
from recipes.application.errors import InvalidServingsError, RecipeNotFoundError
from recipes.application.use_cases.confirm_recipe_preparation import ConfirmRecipePreparation
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.tests.factories import GRAM, make_requirement, make_snapshot
from recipes.tests.fakes import (
    FakeHouseholdInventoryConsumer,
    FakeHouseholdInventoryReader,
    FakeHouseholdRepository,
    FakeRecipeRepository,
    FakeTransactionManager,
)


def _recipe(servings: int) -> RecipeDetail:
    summary = RecipeSummary(
        id=1,
        name="omlet",
        description="",
        servings=servings,
        preparation_time_minutes=5,
        cooking_time_minutes=5,
        difficulty=RecipeDifficulty.EASY,
        category_name=None,
        tag_names=(),
        image_url=None,
    )
    return RecipeDetail(summary=summary, steps=(), ingredients=())


def _build(
    repository: FakeRecipeRepository,
    inventory: list[InventoryItemSnapshot],
    consumer: FakeHouseholdInventoryConsumer,
    transaction_manager: FakeTransactionManager,
) -> ConfirmRecipePreparation:
    return ConfirmRecipePreparation(
        repository,
        FakeHouseholdInventoryReader(inventory),
        consumer,
        transaction_manager,
        HouseholdAccessPolicy(FakeHouseholdRepository({7})),
    )


def test_each_stocked_ingredient_is_consumed_exactly_once() -> None:
    repository = FakeRecipeRepository(
        [_recipe(2)],
        {1: [make_requirement("jajko", "2", GRAM), make_requirement("maka", "50", GRAM)]},
    )
    consumer = FakeHouseholdInventoryConsumer()
    transaction_manager = FakeTransactionManager()
    use_case = _build(
        repository,
        [make_snapshot(1, "jajko", "10", GRAM), make_snapshot(2, "maka", "500", GRAM)],
        consumer,
        transaction_manager,
    )

    use_case.execute(5, 7, 1, 4)

    assert consumer.consumed == [
        (7, 1, Decimal("4"), "g"),
        (7, 2, Decimal("100"), "g"),
    ]
    assert transaction_manager.entered_count == 1


def test_ingredients_absent_from_inventory_are_skipped() -> None:
    repository = FakeRecipeRepository(
        [_recipe(2)],
        {1: [make_requirement("jajko", "2", GRAM), make_requirement("maka", "50", GRAM)]},
    )
    consumer = FakeHouseholdInventoryConsumer()
    use_case = _build(
        repository, [make_snapshot(1, "jajko", "10", GRAM)], consumer, FakeTransactionManager()
    )

    use_case.execute(5, 7, 1, 2)

    assert [entry[1] for entry in consumer.consumed] == [1]


def test_repeated_confirmation_consumes_again() -> None:
    repository = FakeRecipeRepository([_recipe(2)], {1: [make_requirement("jajko", "2", GRAM)]})
    consumer = FakeHouseholdInventoryConsumer()
    transaction_manager = FakeTransactionManager()
    use_case = _build(
        repository, [make_snapshot(1, "jajko", "10", GRAM)], consumer, transaction_manager
    )

    use_case.execute(5, 7, 1, 2)
    use_case.execute(5, 7, 1, 2)

    assert len(consumer.consumed) == 2
    assert transaction_manager.entered_count == 2


def test_non_member_consumes_nothing() -> None:
    repository = FakeRecipeRepository([_recipe(2)], {1: [make_requirement("jajko", "2", GRAM)]})
    consumer = FakeHouseholdInventoryConsumer()
    transaction_manager = FakeTransactionManager()
    use_case = _build(
        repository, [make_snapshot(1, "jajko", "10", GRAM)], consumer, transaction_manager
    )

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(5, 99, 1, 2)

    assert consumer.consumed == []
    assert transaction_manager.entered_count == 0


def test_zero_servings_is_rejected() -> None:
    consumer = FakeHouseholdInventoryConsumer()
    use_case = _build(
        FakeRecipeRepository([_recipe(2)], {}), [], consumer, FakeTransactionManager()
    )

    with pytest.raises(InvalidServingsError):
        use_case.execute(5, 7, 1, 0)

    assert consumer.consumed == []


def test_unknown_recipe_is_rejected() -> None:
    consumer = FakeHouseholdInventoryConsumer()
    use_case = _build(FakeRecipeRepository([], {}), [], consumer, FakeTransactionManager())

    with pytest.raises(RecipeNotFoundError):
        use_case.execute(5, 7, 404, 2)

    assert consumer.consumed == []
