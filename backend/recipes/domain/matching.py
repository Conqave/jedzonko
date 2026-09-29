from dataclasses import dataclass

from recipes.domain.external import (
    ExternalRecipeMatch,
    ExternalRecipePage,
    MatchedExternalRecipePage,
)
from recipes.domain.stock import StockedProduct
from shared.measurement import MeasurementDimension, MeasurementUnit, Quantity


@dataclass(frozen=True, slots=True)
class StockMatch:
    product: StockedProduct
    available: Quantity | None


def find_stock(
    ingredient_id: int | None, target: MeasurementUnit, stock: list[StockedProduct]
) -> StockMatch | None:
    if ingredient_id is None:
        return None
    candidates = [product for product in stock if ingredient_id in product.ingredient_ids]
    if not candidates:
        return None
    ordered = sorted(candidates, key=lambda product: (product.product_name, product.product_id))
    best: StockMatch | None = None
    for product in ordered:
        available = available_quantity(product, target)
        if available is None:
            continue
        if best is None or best.available is None or available.amount > best.available.amount:
            best = StockMatch(product=product, available=available)
    if best is None:
        return StockMatch(product=ordered[0], available=None)
    return best


def has_stock(ingredient_id: int | None, stock: list[StockedProduct]) -> bool:
    if ingredient_id is None:
        return False
    return any(ingredient_id in product.ingredient_ids for product in stock)


def available_quantity(product: StockedProduct, target: MeasurementUnit) -> Quantity | None:
    stock = product.quantity
    if _is_directly_comparable(stock.unit, target):
        return stock.convert_to(target)
    package = product.package_content
    if package is None or not _is_directly_comparable(package.unit, target):
        return None
    return Quantity(amount=stock.amount * package.amount, unit=package.unit).convert_to(target)


def consumption_in_stock_unit(product: StockedProduct, required: Quantity) -> Quantity | None:
    stock_unit = product.quantity.unit
    if _is_directly_comparable(required.unit, stock_unit):
        return required.convert_to(stock_unit)
    package = product.package_content
    if package is None or not _is_directly_comparable(required.unit, package.unit):
        return None
    packages = required.convert_to(package.unit).amount / package.amount
    return Quantity(amount=packages, unit=stock_unit)


def match_external_recipes(
    page: ExternalRecipePage, stock: list[StockedProduct], ingredient_ids: dict[str, int]
) -> MatchedExternalRecipePage:
    matches = []
    for summary in page.recipes:
        wanted = {ingredient_ids[name] for name in summary.tag_names if name in ingredient_ids}
        matched = sorted(
            {product.product_name for product in stock if product.ingredient_ids & wanted}
        )
        matches.append(ExternalRecipeMatch(summary=summary, matched_product_names=tuple(matched)))
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


def _is_directly_comparable(unit: MeasurementUnit, target: MeasurementUnit) -> bool:
    if unit.dimension is not target.dimension:
        return False
    if unit.dimension is MeasurementDimension.COUNT:
        return unit.code == target.code
    return True
