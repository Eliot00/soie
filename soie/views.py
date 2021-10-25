from functools import wraps
from itertools import chain
from typing import Awaitable, Callable, Collection

from typing_extensions import Literal

from .requests import Request
from .responses import Response

AllowMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
View = Callable[[Request], Awaitable[Response]]


def require_http_method(methods: Collection[AllowMethod]):
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
                return Response(headers=headers)
            else:
                return Response(status_code=405, headers=headers)

        return inner

    return decorator
