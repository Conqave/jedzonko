class InvalidNameError(Exception):
    pass


class InvalidProductIngredientError(Exception):
    pass


class InvalidProductClassificationError(Exception):
    pass


class ProductIngredientAlreadyRecordedError(Exception):
    pass


class ProductIngredientNotFoundError(Exception):
    pass


class InvalidProductIngredientTransitionError(Exception):
    pass


class InvalidProductPackageError(Exception):
    pass


class UnknownMeasurementUnitError(Exception):
    pass


class IngredientMergeError(Exception):
    pass


class InvalidTagCaloriesError(Exception):
    pass
