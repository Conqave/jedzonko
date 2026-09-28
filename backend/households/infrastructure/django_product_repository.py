from django.db import IntegrityError

from households.application.errors import DuplicateProductError, ProductNotFoundError
from households.application.ports.product_repository import ProductRepository
from households.domain.product import ProductSummary
from households.domain.product_names import ProductNames
from households.models import Product
from shared.text import normalize_text


class DjangoProductRepository(ProductRepository):
    def list_products(self, household_id: int, name_query: str | None) -> list[ProductSummary]:
        rows = Product.objects.filter(household_id=household_id)
        if name_query is not None:
            rows = rows.filter(normalized_name__contains=normalize_text(name_query))
        return [self._to_summary(row) for row in rows]

    def list_product_names(self, household_id: int) -> list[ProductNames]:
        rows = Product.objects.filter(household_id=household_id).prefetch_related("product_tags__ingredient_tag")
        return [
            ProductNames(
                id=row.pk,
                name=row.name,
                normalized_name=row.normalized_name,
                tag_names=tuple(tag.ingredient_tag.normalized_name for tag in row.product_tags.all()),
            )
            for row in rows
        ]

    def find_product(self, household_id: int, product_id: int) -> ProductSummary | None:
        row = Product.objects.filter(household_id=household_id, pk=product_id).first()
        return None if row is None else self._to_summary(row)

    def find_product_by_name(self, household_id: int, name: str) -> ProductSummary | None:
        row = Product.objects.filter(
            household_id=household_id, normalized_name=normalize_text(name)
        ).first()
        return None if row is None else self._to_summary(row)

    def create_product(
        self, household_id: int, name: str, default_unit_code: str, is_food: bool
    ) -> ProductSummary:
        try:
            row = Product.objects.create(
                household_id=household_id,
                name=name,
                normalized_name=normalize_text(name),
                default_unit_code=default_unit_code,
                is_food=is_food,
            )
        except IntegrityError as error:
            raise DuplicateProductError from error
        return self._to_summary(row)

    def rename_product(self, household_id: int, product_id: int, name: str) -> ProductSummary:
        row = Product.objects.filter(household_id=household_id, pk=product_id).first()
        if row is None:
            raise ProductNotFoundError
        row.name = name
        row.normalized_name = normalize_text(name)
        try:
            row.save(update_fields=["name", "normalized_name", "updated_at"])
        except IntegrityError as error:
            raise DuplicateProductError from error
        return self._to_summary(row)

    def get_or_create_product(
        self, household_id: int, name: str, default_unit_code: str, is_food: bool
    ) -> ProductSummary:
        row, _ = Product.objects.get_or_create(
            household_id=household_id,
            normalized_name=normalize_text(name),
            defaults={
                "name": name,
                "default_unit_code": default_unit_code,
                "is_food": is_food,
            },
        )
        return self._to_summary(row)

    @staticmethod
    def _to_summary(row: Product) -> ProductSummary:
        return ProductSummary(
            id=row.pk,
            household_id=row.household_id,
            name=row.name,
            normalized_name=row.normalized_name,
            default_unit_code=row.default_unit_code,
            is_food=row.is_food,
        )
