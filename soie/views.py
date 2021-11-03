from functools import wraps
from itertools import chain
from typing import Any, Awaitable, Callable, Collection

from typing_extensions import Literal

from .requests import Request
from .responses import JSONResponse, PlainTextResponse, Response

AllowMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
View = Callable[[Request], Awaitable[Response]]


def require_http_method(methods: Collection[AllowMethod]) -> Callable[[View], View]:
    if "GET" in methods:
        allow_methods = set(chain(methods, ("HEAD",)))
    else:
        allow_methods = methods
    headers = {"Allow": ", ".join(allow_methods)}

    def decorator(func: View) -> View:
        @wraps(func)
        async def inner(request: Request) -> Response:
            if request.method in allow_methods:
                return await func(request)
            elif request.method == "OPTIONS":
                return PlainTextResponse(headers=headers)
            else:
                return PlainTextResponse(status_code=405, headers=headers)

        return inner

    return decorator


def auto_json_response(func: Callable[[Request], Awaitable[Any]]) -> View:
    @wraps(func)
    async def inner(request: Request) -> JSONResponse:
        raw_value = await func(request)
        return JSONResponse(raw_value)

    return inner
