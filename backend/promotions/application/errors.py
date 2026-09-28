class InvalidPromotionQueryError(Exception):
    pass


class InvalidShopSelectionError(Exception):
    pass


class PromotionSourceError(Exception):
    pass


class PromotionSourceUnavailableError(PromotionSourceError):
    pass


class PromotionSourceContractError(PromotionSourceError):
    pass
