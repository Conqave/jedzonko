from shopping.application.errors import ShoppingItemMergeConflictError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_subject import ShoppingSubject


class ReassignShoppingIngredient:

    def __init__(self, repository: ShoppingListRepository) -> None:
        self._repository = repository

    def execute(self, source_ingredient_id: int, target_ingredient_id: int) -> None:
        target = ShoppingSubject(ingredient_id=target_ingredient_id)
        for item in self._repository.list_items_about_ingredient(source_ingredient_id):
            existing = (
                None
                if item.is_purchased
                else self._repository.find_pending_item(item.list_id, target)
            )
            if existing is None:
                self._repository.set_item_ingredient(item.id, target_ingredient_id)
                continue
            unit_code = None if existing.unit is None else existing.unit.code
            if unit_code != (None if item.unit is None else item.unit.code):
                raise ShoppingItemMergeConflictError
            self._repository.set_item_quantity(
                existing.id, existing.quantity + item.quantity, unit_code
            )
            self._repository.delete_item(item.id)
