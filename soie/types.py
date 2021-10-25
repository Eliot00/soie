from typing import Any, Awaitable, Callable, MutableMapping

from typing_extensions import TypeAlias

Scope: TypeAlias = MutableMapping[str, Any]
Message: TypeAlias = MutableMapping[str, Any]
Receive: TypeAlias = Callable[[], Awaitable[Message]]
Send: TypeAlias = Callable[[Message], Awaitable[None]]
ASGIApp: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]
