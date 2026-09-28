from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request


def current_user_id(request: Request) -> int:
    user_id = request.user.pk
    if user_id is None:
        raise NotAuthenticated
    return int(user_id)
