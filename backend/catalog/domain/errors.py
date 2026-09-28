class InvalidIngredientNameError(Exception):
    pass


class InvalidProductIngredientError(Exception):
    pass


class InvalidProductClassificationError(Exception):
    pass


class ProductAlreadyClassifiedError(Exception):
    pass


class ProductIngredientAlreadyRecordedError(Exception):
    pass


class ProductIngredientNotFoundError(Exception):
    pass


class InvalidProductIngredientTransitionError(Exception):
    pass
