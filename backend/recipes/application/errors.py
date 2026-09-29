class RecipeNotFoundError(Exception):
    pass


class MeasurementUnitNotFoundError(Exception):
    pass


class DuplicateRecipeIngredientError(Exception):
    pass


class RecipeCategoryNotFoundError(Exception):
    pass


class InvalidServingsError(Exception):
    pass


class RecipeSourceError(Exception):
    pass


class RecipeSourceUnavailableError(RecipeSourceError):
    pass


class RecipeSourceContractError(RecipeSourceError):
    pass


class RecipeNotFoundAtSourceError(RecipeSourceError):
    pass


class IngredientLineInterpreterError(Exception):
    pass


class IngredientLineInterpreterUnavailableError(IngredientLineInterpreterError):
    pass


class IngredientLineInterpreterContractError(IngredientLineInterpreterError):
    pass
