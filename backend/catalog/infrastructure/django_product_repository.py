from decimal import Decimal

from django.db import IntegrityError
from django.db.models import Count, Q

from catalog.application.errors import DuplicateProductError, ProductNotFoundError
from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.names import CatalogName
from catalog.domain.product import Product, ProductListing, ProductPackage, ProductTag
from catalog.domain.product_ingredient import ProductIngredientStatus
from catalog.models import Product as ProductRow
from catalog.models import ProductIngredient as ProductIngredientRow

CONFIRMED = ProductIngredientStatus.CONFIRMED.value
PROPOSED = ProductIngredientStatus.PROPOSED.value


class DjangoProductRepository(ProductRepository):
    def find(self, product_id: int) -> Product | None:
        row = ProductRow.objects.filter(pk=product_id).first()
        return None if row is None else _to_product(row)

    def find_by_name(self, household_id: int, normalized_name: str) -> Product | None:
        row = ProductRow.objects.filter(
            household_id=household_id, normalized_name=normalized_name
        ).first()
        return None if row is None else _to_product(row)

    def list_listings(
        self, household_id: int, normalized_search: str | None
    ) -> list[ProductListing]:
        rows = ProductRow.objects.filter(household_id=household_id).annotate(
            open_proposals=Count("ingredient_links", filter=Q(ingredient_links__status=PROPOSED))
        )
        if normalized_search is not None:
            rows = rows.filter(normalized_name__contains=normalized_search)
        links = ProductIngredientRow.objects.filter(
            product__household_id=household_id, status=CONFIRMED
        ).select_related("ingredient")
        tags: dict[int, list[ProductTag]] = {}
        for link in links:
            tag = ProductTag(ingredient_id=link.ingredient_id, name=link.ingredient.name)
            tags.setdefault(link.product_id, []).append(tag)
        listings = []
        for row in rows:
            product = _to_product(row)
            product_tags = tuple(sorted(tags.get(row.pk, []), key=lambda tag: tag.name))
            listings.append(
                ProductListing(
                    product=product, tags=product_tags, open_proposal_count=row.open_proposals
                )
            )
        return listings

    def list_for_household(self, household_id: int) -> list[Product]:
        return [_to_product(row) for row in ProductRow.objects.filter(household_id=household_id)]

    def list_unclassified(self) -> list[Product]:
        rows = (
            ProductRow.objects.filter(household__deleted_at__isnull=True, is_food=True)
            .exclude(ingredient_links__status=CONFIRMED)
            .order_by("created_at", "pk")
        )
        return [_to_product(row) for row in rows]

    def create(
        self,
        household_id: int,
        name: CatalogName,
        default_unit_code: str,
        is_food: bool,
        package: ProductPackage | None,
    ) -> Product:
        try:
            row = ProductRow.objects.create(
                household_id=household_id,
                name=name.name,
                normalized_name=name.normalized_name,
                default_unit_code=default_unit_code,
                is_food=is_food,
                package_quantity=None if package is None else package.quantity,
                package_unit_code=None if package is None else package.unit_code,
            )
        except IntegrityError as error:
            raise DuplicateProductError from error
        return _to_product(row)

    def delete(self, product_id: int) -> None:
        ProductRow.objects.filter(pk=product_id).delete()

    def update(self, product_id: int, name: CatalogName, package: ProductPackage | None) -> Product:
        row = ProductRow.objects.filter(pk=product_id).first()
        if row is None:
            raise ProductNotFoundError
        row.name = name.name
        row.normalized_name = name.normalized_name
        row.package_quantity = None if package is None else package.quantity
        row.package_unit_code = None if package is None else package.unit_code
        try:
            row.save()
        except IntegrityError as error:
            raise DuplicateProductError from error
        return _to_product(row)


def _to_product(row: ProductRow) -> Product:
    package = _to_package(row.package_quantity, row.package_unit_code)
    return Product(
        id=row.pk,
        household_id=row.household_id,
        name=row.name,
        default_unit_code=row.default_unit_code,
        is_food=row.is_food,
        package=package,
    )


def _to_package(quantity: Decimal | None, unit_code: str | None) -> ProductPackage | None:
    if quantity is None or unit_code is None:
        return None
    return ProductPackage(quantity=quantity, unit_code=unit_code)
