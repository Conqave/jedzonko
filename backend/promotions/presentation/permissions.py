from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from promotions.application.permissions import VIEW_PROMOTIONS_PERMISSION


class CanViewPromotions(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.has_perm(VIEW_PROMOTIONS_PERMISSION)
