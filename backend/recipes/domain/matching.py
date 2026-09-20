from inventory.domain.models import InventoryItemSnapshot
from recipes.domain.external import (
    ExternalRecipeMatch,
    ExternalRecipePage,
    MatchedExternalRecipePage,
)
from shared.measurement import MeasurementDimension, MeasurementUnit, Quantity
from shared.text import normalize_text


def matches_product(normalized_name: str, item: InventoryItemSnapshot) -> bool:
    if normalized_name in item.alias_names:
        return True
    required_words = normalized_name.split()
    if not required_words:
        return False
    product_words = set(item.normalized_name.split())
    return all(word in product_words for word in required_words)


def find_matching_item(
    normalized_name: str, inventory: list[InventoryItemSnapshot]
) -> InventoryItemSnapshot | None:
    matches = [item for item in inventory if matches_product(normalized_name, item)]
    if not matches:
        return None
    return min(matches, key=lambda item: _match_order(normalized_name, item))


def find_available_quantity(
    item: InventoryItemSnapshot, target: MeasurementUnit
) -> Quantity | None:
    stock = item.as_quantity()
    if _is_directly_comparable(stock.unit, target):
        return stock.convert_to(target)
    package = item.package_content()
    if package is None:
        return None
    content = Quantity(amount=stock.amount * package.amount, unit=package.unit)
    if not _is_directly_comparable(content.unit, target):
        return None
    return content.convert_to(target)


def find_matched_product_names(
    tag_names: tuple[str, ...], inventory: list[InventoryItemSnapshot]
) -> tuple[str, ...]:
    matched: set[str] = set()
    for tag_name in tag_names:
        item = find_matching_item(normalize_text(tag_name), inventory)
        if item is not None:
            matched.add(item.product_name)
    return tuple(sorted(matched))


def match_external_recipes(
    page: ExternalRecipePage, inventory: list[InventoryItemSnapshot]
) -> MatchedExternalRecipePage:
    matches = [
        ExternalRecipeMatch(
            summary=summary,
            matched_product_names=find_matched_product_names(summary.tag_names, inventory),
        )
        for summary in page.recipes
    ]
    matches.sort(
        key=lambda match: (
            -len(match.matched_product_names),
            match.summary.name,
            match.summary.reference,
        )
    )
    return MatchedExternalRecipePage(
        matches=tuple(matches),
        page=page.page,
        page_size=page.page_size,
        total_count=page.total_count,
        total_pages=page.total_pages,
    )


def _match_order(normalized_name: str, item: InventoryItemSnapshot) -> tuple[bool, int, str, int]:
    return (
        normalized_name not in item.alias_names,
        len(item.normalized_name),
        item.normalized_name,
        item.id,
    )


def _is_directly_comparable(unit: MeasurementUnit, target: MeasurementUnit) -> bool:
    if unit.dimension is not target.dimension:
        return False
    if unit.dimension is MeasurementDimension.COUNT:
        return unit.code == target.code
    return True
