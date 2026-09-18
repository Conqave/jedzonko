from rest_framework.response import Response
from rest_framework.views import exception_handler


def _resolve_code(exc: Exception) -> str:
    detail = getattr(exc, "detail", None)
    code = getattr(detail, "code", None)
    if code is None and isinstance(detail, list) and detail:
        code = getattr(detail[0], "code", None)
    if code is None:
        code = getattr(exc, "default_code", "error")
    return str(code)


def handle_api_exception(exc: Exception, context: dict[str, object]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None
    payload: dict[str, object] = {"code": _resolve_code(exc)}
    if isinstance(response.data, dict) and "detail" in response.data:
        payload["detail"] = str(response.data["detail"])
    elif isinstance(response.data, list) and len(response.data) == 1:
        payload["detail"] = str(response.data[0])
    else:
        payload["detail"] = "Request failed."
        payload["errors"] = response.data
    response.data = payload
    return response
