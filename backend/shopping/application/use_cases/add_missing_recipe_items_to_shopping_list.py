from households.application.access import HouseholdAccessPolicy
from shopping.application.errors import ShoppingListNotFoundError
from shopping.application.ports.product_resolver import ProductResolver
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class AddMissingRecipeItemsToShoppingList:
    def __init__(
        self,
        repository: ShoppingListRepository,
        access: HouseholdAccessPolicy,
        recipes: RecipeRequirementReader,
        products: ProductResolver,
    ) -> None:
        self._repository = repository
        self._access = access
        self._recipes = recipes
        self._products = products

    def execute(
        self, user_id: int, list_id: int, recipe_id: int, servings: int
    ) -> list[ShoppingItemSnapshot]:
        household_id = self._repository.find_household_id_for_list(list_id)
        if household_id is None:
            raise ShoppingListNotFoundError
        self._access.require_membership(user_id, household_id)
        missing_items = self._recipes.read_missing_items(user_id, household_id, recipe_id, servings)
        for missing in missing_items:
            product_id = self._products.resolve_product_id(
                household_id, missing.name, missing.unit_code
            )
            existing = self._repository.find_pending_item_by_product(list_id, product_id)
            if existing is None:
                self._repository.add_item(
                    list_id, product_id, None, missing.amount, missing.unit_code
                )
                continue
            same_unit = existing.unit is not None and existing.unit.code == missing.unit_code
            if same_unit and existing.quantity >= missing.amount:
                continue
            self._repository.set_item_quantity(existing.id, missing.amount, missing.unit_code)
        return self._repository.list_items(list_id)
