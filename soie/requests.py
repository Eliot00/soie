from __future__ import annotations

from functools import cache
from typing import Any
from urllib.parse import parse_qsl

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

    @property
    @cache
    def query_params(self) -> QueryParams:
        return QueryParams(self["query_string"])


class QueryParams:
    def __init__(self, query_string: bytes) -> None:
        print(query_string)
        self._dict = {
            key.decode("utf-8"): value.decode("utf-8") for key, value in parse_qsl(query_string, keep_blank_values=True)
        }

    def __getitem__(self, key: str) -> str:
        return self._dict[key]
