from __future__ import annotations

import dataclasses
import inspect
import traceback
from typing import Any, Awaitable, Callable, List, Union

from typing_extensions import Literal, TypeAlias

from .exceptions import ErrorHandlers, ExceptionContextManager
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
        err_handlers: ErrorHandlers = None,
    ):
        self.debug = debug
        self.lifespan = LifeSpan(on_startup or [], on_shutdown or [])
        if router is None:
            router = Router()
        self.router = router
        self.err_handlers = err_handlers

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type: Literal["lifespan", "http", "websocket"] = scope["type"]
        return await getattr(self, scope_type)(scope, receive, send)

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with ExceptionContextManager(scope, receive, send, self.err_handlers):
            endpoint = self.router.get_endpoint(scope["path"])
            request = Request(scope, receive)
            response = await endpoint(request)
            await response(scope, receive, send)

    async def websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        raise NotImplementedError

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["app"] = self

        await self.app(scope, receive, send)
