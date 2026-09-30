class InvalidPromotionQueryError(Exception):
    pass


class InvalidShopSelectionError(Exception):
    pass


class UnknownShopError(Exception):
    def __init__(self, shop_slug: str) -> None:
        super().__init__(f"unknown shop: {shop_slug}")
        self.shop_slug = shop_slug


class PromotionSourceUnavailableError(Exception):
    pass


class PromotionSourceContractError(Exception):
    pass
