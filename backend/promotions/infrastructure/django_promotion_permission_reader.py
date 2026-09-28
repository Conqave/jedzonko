from django.contrib.auth.models import User

from promotions.application.permissions import VIEW_PROMOTIONS_PERMISSION
from promotions.application.ports.promotion_permission_reader import PromotionPermissionReader


class DjangoPromotionPermissionReader(PromotionPermissionReader):
    def can_view_promotions(self, user_id: int) -> bool:
        user = User.objects.filter(pk=user_id, is_active=True).first()
        return user is not None and user.has_perm(VIEW_PROMOTIONS_PERMISSION)
