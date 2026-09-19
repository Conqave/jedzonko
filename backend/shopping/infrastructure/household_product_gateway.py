from households.composition import (
    build_find_household_product,
    build_resolve_household_product,
)
from shopping.application.ports.product_resolver import ProductResolver


class HouseholdProductGateway(ProductResolver):
    def resolve_product_id(self, household_id: int, name: str, default_unit_code: str) -> int:
        product = build_resolve_household_product().execute(
            household_id, name, default_unit_code, True
        )
        return product.id

    def is_household_product(self, household_id: int, product_id: int) -> bool:
        return build_find_household_product().execute(household_id, product_id) is not None
