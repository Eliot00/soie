from functools import cache
from typing import Any

from .types import Receive, Scope


class Request:
    """
    Request wrapped ASGI's request information.
    """

    def __init__(self, scope: Scope, receive: Receive) -> None:
        self._scope = scope
        self._receive = receive

    def __getitem__(self, key: str) -> Any:
        return self._scope[key]

    @property
    @cache
    def method(self) -> str:
        return self._scope["method"]
