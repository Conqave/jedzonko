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


class NoShopsChosenError(Exception):
    pass


class NothingToSplitError(Exception):
    pass


class PromotionsNotAllowedError(Exception):
    pass


class PromotionsUnavailableError(Exception):
    pass


class ExternalRecipeNotFoundError(Exception):
    pass


class RecipesUnavailableError(Exception):
    pass


class TaggingUnavailableError(Exception):
    pass
