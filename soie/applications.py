from __future__ import annotations

import dataclasses
import inspect
import traceback
from typing import Any, Awaitable, Callable, List, Optional, Union

from typing_extensions import Literal, TypeAlias

from .exceptions import (
    ExceptionContextManager,
    ExceptionHandler,
    ExceptionHandlers,
    HTTPException,
)
from .requests import Request
from .routing import Router
from .types import Receive, Scope, Send

LifeSpanHook: TypeAlias = Union[Callable[[], Any], Callable[[], Awaitable[Any]]]


@dataclasses.dataclass
class LifeSpan:
    on_startup: List[LifeSpanHook] = dataclasses.field(default_factory=list)
    on_shutdown: List[LifeSpanHook] = dataclasses.field(default_factory=list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        message = await receive()
        assert message["type"] == "lifespan.startup"
        try:
            for handler in self.on_startup:
                result = handler()
                if inspect.isawaitable(result):
                    await result
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.startup.failed", "message": msg})
            raise
        await send({"type": "lifespan.startup.completed"})

        message = await receive()
        assert message["type"] == "lifespan.shutdown"
        try:
            for handler in self.on_shutdown:
                result = handler()
                if inspect.isawaitable(result):
                    await result
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.shutdown.failed", "message": msg})
            raise
        await send({"type": "lifespan.shutdown.completed"})


class Soie:
    def __init__(
        self,
        *,
        debug: bool = False,
        on_startup: List[LifeSpanHook] = None,
        on_shutdown: List[LifeSpanHook] = None,
        router: Router = None,
        exception_handlers: Optional[ExceptionHandlers] = None,
    ):
        self.debug = debug
        self.lifespan = LifeSpan(on_startup or [], on_shutdown or [])
        if router is None:
            router = Router()
        self.router = router
        if exception_handlers is None:
            exception_handlers = {}
        self._exception_handlers: ExceptionHandlers = {HTTPException: HTTPException.to_response} | exception_handlers

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type: Literal["lifespan", "http", "websocket"] = scope["type"]
        return await getattr(self, scope_type)(scope, receive, send)

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with ExceptionContextManager(self._exception_handlers, scope, receive, send):
            route = self.router.get_route(scope["path"])
            request = Request(scope, receive)
            response = await route.endpoint(request)
            await response(scope, receive, send)

    async def websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        raise NotImplementedError

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        await self.app(scope, receive, send)

    def add_exception_handler(self, exc_type: type[BaseException], handler: ExceptionHandler) -> None:
        self._exception_handlers[exc_type] = handler

    def exception_handler(self, exc_type: type[BaseException]) -> Callable[[ExceptionHandler], ExceptionHandler]:
        def decorator(handler: ExceptionHandler) -> ExceptionHandler:
            self.add_exception_handler(exc_type, handler)
            return handler

        return decorator
