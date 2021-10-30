from functools import wraps
from itertools import chain
from typing import Any, Awaitable, Callable, Collection, Iterator

from typing_extensions import Literal

from .requests import Request
from .responses import PlainTextResponse, Response

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


def inject_path_params(params: Iterator[tuple[str, Any]], func: View) -> View:
    @wraps(func)
    async def inner(request: Request) -> Response:
        request.path_params = {key: value for key, value in params}
        return await func(request)

    return inner


class ClassView:
    pass
