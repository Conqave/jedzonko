from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from config.composition import container


class CanViewPromotions(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user_id = request.user.pk
        if user_id is None:
            return False
        use_case = container().promotions.check_promotion_access
        return use_case.execute(int(user_id))
