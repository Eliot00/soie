from __future__ import annotations

from http import HTTPStatus
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional, Type, TypeVar

from typing_extensions import TypeAlias

from .responses import Response
from .types import Receive, Scope, Send


class SoieException(Exception):
    """Base Error"""

    pass


class HTTPException(SoieException):
    def __init__(
        self, status_code: int = 400, headers: Optional[Mapping[str, str]] = None, content: Any = None
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        if content is None:
            content = HTTPStatus(status_code).description
        self.content = content
        super().__init__(status_code, content)


Error = TypeVar("Error", bound=BaseException)
ErrorHandlers: TypeAlias = Dict[Type[Error], Callable[[Error], Awaitable[Response]]]


async def http_error_to_response(e: HTTPException) -> Response:
    return Response(content=e.content, status_code=e.status_code, headers=e.headers)


class ExceptionContextManager:
    def __init__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        err_handlers: ErrorHandlers = None,
    ):
        self.err_handlers = {HTTPException: http_error_to_response}
        if err_handlers is not None:
            self.err_handlers |= err_handlers
        self._asgi_context = (scope, receive, send)

    async def __aenter__(self) -> ExceptionContextManager:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            return True
        convertor = self.err_handlers.get(exc_type)
        if convertor is None:
            return False
        response = await convertor(exc_val)
        await response(*self._asgi_context)
        return True
