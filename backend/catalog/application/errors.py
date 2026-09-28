class IngredientNotFoundError(Exception):
    pass


class DuplicateIngredientNameError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class DuplicateProductError(Exception):
    pass


class CandidateNotFoundError(Exception):
    pass


class CandidateAlreadyDecidedError(Exception):
    pass


class IngredientClassifierError(Exception):
    pass


class IngredientClassifierUnavailableError(IngredientClassifierError):
    pass


class IngredientClassifierContractError(IngredientClassifierError):
    pass
