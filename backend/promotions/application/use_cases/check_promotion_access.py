from promotions.application.ports.promotion_permission_reader import PromotionPermissionReader


class CheckPromotionAccess:
    def __init__(self, permissions: PromotionPermissionReader) -> None:
        self._permissions = permissions

    def execute(self, user_id: int) -> bool:
        return self._permissions.can_view_promotions(user_id)
