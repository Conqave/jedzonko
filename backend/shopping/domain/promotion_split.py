from dataclasses import dataclass

from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot

REMAINING_GROUP_NAME = "Pozostałe"


@dataclass(frozen=True, slots=True)
class ShopPromotions:
    shop_slug: str
    shop_name: str
    promoted_names: frozenset[str]


@dataclass(frozen=True, slots=True)
class ShoppingGroup:
    name: str
    items: tuple[ShoppingItemSnapshot, ...]


def split_by_promotions(
    items: list[ShoppingItemSnapshot], shops_in_preference_order: list[ShopPromotions]
) -> list[ShoppingGroup]:
    assigned: dict[str, list[ShoppingItemSnapshot]] = {
        shop.shop_slug: [] for shop in shops_in_preference_order
    }
    remaining: list[ShoppingItemSnapshot] = []
    for item in items:
        name = item.name.strip()
        shop = next(
            (each for each in shops_in_preference_order if name in each.promoted_names), None
        )
        if shop is None:
            remaining.append(item)
            continue
        assigned[shop.shop_slug].append(item)
    groups = [
        ShoppingGroup(name=shop.shop_name, items=tuple(assigned[shop.shop_slug]))
        for shop in shops_in_preference_order
        if assigned[shop.shop_slug]
    ]
    if remaining:
        groups.append(ShoppingGroup(name=REMAINING_GROUP_NAME, items=tuple(remaining)))
    return groups
