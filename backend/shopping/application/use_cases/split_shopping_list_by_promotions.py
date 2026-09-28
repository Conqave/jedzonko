from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import (
    NoShopsChosenError,
    NothingToSplitError,
    ShoppingListNotFoundError,
)
from shopping.application.ports.promotion_coverage_reader import PromotionCoverageReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.promotion_split import split_by_promotions
from shopping.domain.shopping_list_summary import ShoppingListSummary

SPLIT_LIST_PREFIX = "Zakupy — "


class SplitShoppingListByPromotions:
    def __init__(
        self,
        repository: ShoppingListRepository,
        promotions: PromotionCoverageReader,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._promotions = promotions
        self._memberships = memberships
        self._transactions = transactions

    def execute(
        self, user_id: int, list_id: int, shop_slugs: tuple[str, ...]
    ) -> list[ShoppingListSummary]:
        if not shop_slugs:
            raise NoShopsChosenError
        shopping_list = self._repository.find_list(list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        pending = self._repository.list_pending_items(list_id)
        if not pending:
            raise NothingToSplitError
        stripped_names = [item.name.strip() for item in pending]
        unique_names = dict.fromkeys(stripped_names)
        names = tuple(unique_names)
        shops = self._promotions.get_shop_promotions(user_id, names, shop_slugs)
        shops_by_slug = {shop.shop_slug: shop for shop in shops}
        preferred = [shops_by_slug[slug] for slug in shop_slugs if slug in shops_by_slug]
        groups = split_by_promotions(pending, preferred)
        created: list[ShoppingListSummary] = []
        with self._transactions.atomic():
            for group in groups:
                name = f"{SPLIT_LIST_PREFIX}{group.name}"
                new_list = self._repository.create_list(
                    shopping_list.household_id, name, is_primary=False
                )
                for item in group.items:
                    unit_code = None if item.unit is None else item.unit.code
                    self._repository.add_item(new_list.id, item.subject, item.quantity, unit_code)
                created.append(new_list)
        return [self._summary(each.id) for each in created]

    def _summary(self, list_id: int) -> ShoppingListSummary:
        summary = self._repository.find_list(list_id)
        if summary is None:
            raise ShoppingListNotFoundError
        return summary
