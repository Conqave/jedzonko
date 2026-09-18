from rest_framework.response import Response
from rest_framework.views import exception_handler


def handle_api_exception(exc: Exception, context: dict[str, object]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None
    code = getattr(exc, "default_code", "error")
    detail = getattr(exc, "detail", None)
    payload: dict[str, object] = {"code": str(getattr(detail, "code", code))}
    if isinstance(response.data, dict) and "detail" in response.data:
        payload["detail"] = str(response.data["detail"])
    else:
        payload["detail"] = "Request failed."
        payload["errors"] = response.data
    response.data = payload
    return response
