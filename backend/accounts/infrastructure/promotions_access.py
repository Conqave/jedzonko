from accounts.application.ports.promotion_access import PromotionAccess
from promotions.application.use_cases.check_promotion_access import CheckPromotionAccess


class PromotionsAccess(PromotionAccess):
    def __init__(self, check_access: CheckPromotionAccess) -> None:
        self._check_access = check_access

    def can_view_promotions(self, user_id: int) -> bool:
        return self._check_access.execute(user_id)
