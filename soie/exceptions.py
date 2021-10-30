from __future__ import annotations

from http import HTTPStatus
from typing import Awaitable, Callable, Dict, Mapping, Optional, Type, TypeVar

from typing_extensions import TypeAlias

from .responses import JSONResponse, Response
from .types import Receive, Scope, Send


class SoieException(Exception):
    """Base Error"""

    pass


class HTTPException(SoieException):
    def __init__(
        self,
        status_code: int = 400,
        headers: Optional[Mapping[str, str]] = None,
        content: Optional[str | dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        if content is None:
            content = HTTPStatus(status_code).description
        self.content = content
        super().__init__(status_code, content)

    async def to_response(self) -> JSONResponse:
        return JSONResponse(self.content, status_code=self.status_code, headers=self.headers)


class ParamNotMatched(SoieException):
    pass


E = TypeVar("E", bound=BaseException)
ExceptionHandler = Callable[[E], Awaitable[Response]]
ExceptionHandlers: TypeAlias = Dict[Type[E], ExceptionHandler]


class ExceptionContextManager:
    def __init__(
        self,
        exception_handlers: ExceptionHandlers,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):
        self.exception_handlers = exception_handlers
        self._scope = scope
        self._receive = receive
        self._send = send

    async def __aenter__(self) -> ExceptionContextManager:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            return True
        convertor = self.exception_handlers.get(exc_type)
        if convertor is None:
            return False
        response = await convertor(exc_val)
        await response(self._scope, self._receive, self._send)
        return True
