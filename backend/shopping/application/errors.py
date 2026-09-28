class ShoppingListNotFoundError(Exception):
    pass


class ShoppingListItemNotFoundError(Exception):
    pass


class InvalidShoppingItemError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class IngredientNotFoundError(Exception):
    pass


class PrimaryShoppingListNotFoundError(Exception):
    pass


class PrimaryShoppingListCannotBeDeletedError(Exception):
    pass


class ShoppingItemAlreadyPendingError(Exception):
    pass


class ShoppingItemMergeConflictError(Exception):
    pass
