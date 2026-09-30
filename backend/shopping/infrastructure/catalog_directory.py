from catalog.application.use_cases.describe_household_products import DescribeHouseholdProducts
from catalog.application.use_cases.find_household_product import FindHouseholdProduct
from catalog.application.use_cases.get_ingredients import GetIngredients
from shopping.application.ports.catalog_directory import CatalogDirectory as CatalogDirectoryPort


class CatalogDirectory(CatalogDirectoryPort):
    def __init__(
        self,
        find_product: FindHouseholdProduct,
        get_ingredients: GetIngredients,
        describe_products: DescribeHouseholdProducts,
    ) -> None:
        self._find_product = find_product
        self._get_ingredients = get_ingredients
        self._describe_products = describe_products

    def is_household_product(self, household_id: int, product_id: int) -> bool:
        return self._find_product.execute(household_id, product_id) is not None

    def has_ingredient(self, ingredient_id: int) -> bool:
        return ingredient_id in self._get_ingredients.execute({ingredient_id})

    def find_ingredient_name(self, ingredient_id: int) -> str | None:
        ingredient = self._get_ingredients.execute({ingredient_id}).get(ingredient_id)
        return None if ingredient is None else ingredient.name

    def list_products_of_ingredient(self, household_id: int, ingredient_id: int) -> tuple[int, ...]:
        identities = self._describe_products.execute(household_id)
        return tuple(
            identity.product_id
            for identity in identities.values()
            if any(tag.ingredient_id == ingredient_id for tag in identity.tags)
        )
