from decimal import Decimal

import pytest

from shopping.application.errors import NoShopsChosenError, NothingToSplitError
from shopping.application.ports.promotion_coverage_reader import PromotionCoverageReader
from shopping.application.use_cases.create_primary_shopping_list import CreatePrimaryShoppingList
from shopping.application.use_cases.split_shopping_list_by_promotions import (
    SplitShoppingListByPromotions,
)
from shopping.domain.promotion_split import ShopPromotions
from shopping.domain.shopping_subject import ShoppingSubject
from shopping.tests.fakes import (
    FakeHouseholdMembershipReader,
    FakeShoppingListRepository,
    FakeTransactionManager,
)

ALA = 1
HOME = 10
BIEDRONKA = ShopPromotions("biedronka", "Biedronka", frozenset({"masło", "mleko"}))
LIDL = ShopPromotions("lidl", "Lidl", frozenset({"mleko", "chleb"}))


class FakePromotionCoverageReader(PromotionCoverageReader):
    def __init__(self, shops: list[ShopPromotions]) -> None:
        self._shops = shops
        self.asked: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def get_shop_promotions(
        self, user_id: int, item_names: tuple[str, ...], shop_slugs: tuple[str, ...]
    ) -> list[ShopPromotions]:
        self.asked.append((item_names, shop_slugs))
        return [shop for shop in self._shops if shop.shop_slug in shop_slugs]


class Setup:
    def __init__(self) -> None:
        self.repository = FakeShoppingListRepository()
        self.primary = CreatePrimaryShoppingList(self.repository).execute(HOME).id
        self.promotions = FakePromotionCoverageReader([BIEDRONKA, LIDL])
        self.split = SplitShoppingListByPromotions(
            self.repository,
            self.promotions,
            FakeHouseholdMembershipReader({(ALA, HOME)}),
            FakeTransactionManager(),
        )

    def add(self, text: str) -> None:
        subject = ShoppingSubject(free_text=text)
        self.repository.add_item(self.primary, subject, Decimal("1"), None)

    def contents(self, shop_slugs: tuple[str, ...]) -> dict[str, list[str]]:
        created = self.split.execute(ALA, self.primary, shop_slugs)
        return {
            each.name: [item.name for item in self.repository.list_items(each.id)]
            for each in created
        }


@pytest.fixture
def setup() -> Setup:
    return Setup()


def test_each_item_goes_to_the_first_preferred_shop_that_promotes_it(setup: Setup) -> None:
    for text in ["mleko", "masło", "chleb", "ręczniki"]:
        setup.add(text)

    contents = setup.contents(("lidl", "biedronka"))

    assert contents == {
        "Zakupy — Lidl": ["mleko", "chleb"],
        "Zakupy — Biedronka": ["masło"],
        "Zakupy — Pozostałe": ["ręczniki"],
    }


def test_the_original_list_is_kept(setup: Setup) -> None:
    setup.add("mleko")

    setup.contents(("biedronka",))

    assert [item.name for item in setup.repository.list_items(setup.primary)] == ["mleko"]


def test_a_shop_with_nothing_to_buy_gets_no_list(setup: Setup) -> None:
    setup.add("masło")

    contents = setup.contents(("lidl", "biedronka"))

    assert list(contents) == ["Zakupy — Biedronka"]


def test_splitting_needs_shops_and_items(setup: Setup) -> None:
    with pytest.raises(NothingToSplitError):
        setup.split.execute(ALA, setup.primary, ("lidl",))
    setup.add("mleko")
    with pytest.raises(NoShopsChosenError):
        setup.split.execute(ALA, setup.primary, ())


def test_each_name_is_asked_about_once(setup: Setup) -> None:
    setup.add("mleko")
    setup.add("mleko")

    setup.contents(("lidl",))

    assert setup.promotions.asked == [(("mleko",), ("lidl",))]
