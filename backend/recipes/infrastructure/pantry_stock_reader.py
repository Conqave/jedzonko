from catalog.application.use_cases.describe_household_products import DescribeHouseholdProducts
from catalog.domain.product import ProductPackage
from inventory.application.use_cases.get_household_inventory import GetHouseholdInventory
from recipes.application.errors import MeasurementUnitNotFoundError
from recipes.application.ports.household_stock_reader import HouseholdStockReader
from recipes.domain.stock import StockedProduct
from shared.measurement import Quantity
from shared.measurement_units import find_measurement_unit


class PantryStockReader(HouseholdStockReader):

    def __init__(
        self, inventory: GetHouseholdInventory, products: DescribeHouseholdProducts
    ) -> None:
        self._inventory = inventory
        self._products = products

    def get_stock(self, user_id: int, household_id: int) -> list[StockedProduct]:
        items = self._inventory.execute(user_id, household_id)
        identities = self._products.execute(household_id)
        stock = []
        for item in items:
            identity = identities[item.product_id]
            quantity = item.as_quantity()
            package_content = _to_package_content(identity.package)
            stock.append(
                StockedProduct(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    ingredient_ids=frozenset(tag.ingredient_id for tag in identity.tags),
                    tag_names=tuple(tag.name for tag in identity.tags),
                    quantity=quantity,
                    package_content=package_content,
                )
            )
        return stock


def _to_package_content(package: ProductPackage | None) -> Quantity | None:
    if package is None:
        return None
    unit = find_measurement_unit(package.unit_code)
    if unit is None:
        raise MeasurementUnitNotFoundError
    return Quantity(amount=package.quantity, unit=unit)
