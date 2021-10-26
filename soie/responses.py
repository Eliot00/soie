from __future__ import annotations

import json
from abc import ABC, abstractmethod
from http.cookies import SimpleCookie
from typing import (
    Any,
    AnyStr,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from typing_extensions import Literal

from soie.types import Receive, Scope, Send

from . import status

_C = TypeVar("_C")


class Response(ABC, Generic[_C]):
    media_type = "text/plain"
    charset = "utf-8"

    def __init__(
        self,
        content: _C = b"",
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        charset: Optional[str] = None,
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.headers = MutableHeaders(headers)
        self.cookies = SimpleCookie()
        if media_type is not None:
            self.media_type = media_type
        if charset is not None:
            self.charset = charset

    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: int = None,
        expires: int = None,
        path: str = "/",
        domain: str = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Literal["strict", "lax", "none"] = "lax",
    ) -> None:
        cookies = self.cookies
        cookies[key] = value
        if max_age is not None:
            cookies[key]["max_age"] = max_age
        if expires is not None:
            cookies[key]["expires"] = expires
        if path is not None:
            cookies[key]["path"] = path
        if domain is not None:
            cookies[key]["domain"] = domain
        if secure:
            cookies[key]["secure"] = True
        if httponly:
            cookies[key]["httponly"] = True
        if samesite is not None:
            cookies[key]["samesite"] = samesite

    def delete_cookie(self, key: str, path: str = "/", domain: str = None) -> None:
        self.set_cookie(key, expires=0, max_age=0, path=path, domain=domain)

    @abstractmethod
    async def serialize_content(self, content: _C) -> bytes:
        ...

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        body = await self.serialize_content(self.content)
        if "content-length" not in self.headers:
            content_length = str(len(body))
            self.headers["content-length"] = content_length
        content_type = self.media_type
        if content_type and "cotent-type" not in self.headers:
            if content_type.startswith("text/"):
                content_type += "; charset=" + self.charset
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": [
                    *((key.encode("latin-1"), value.encode("latin-1")) for key, value in self.headers.items()),
                    *((b"set-cookie", c.output(header="").encode("latin-1")) for c in self.cookies.values()),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


class PlainTextResponse(Response[AnyStr]):
    media_type = "text/plain"

    async def serialize_content(self, content: AnyStr) -> bytes:
        return content if isinstance(content, bytes) else content.encode(self.charset)


class JSONResponse(Response[Any]):
    """
    Note: Python now does not have a elegant *jsonable* type, hence the content's type is Any.
    """

    media_type = "application/json"

    def __init__(
        self,
        content: Any,
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Mapping[str, str]] = None,
        **json_kwargs: Any,
    ) -> None:
        self.json_kwargs = {
            "ensure_ascii": False,
            "allow_nan": False,
            "indent": None,
            "separators": (",", ":"),
            "default": None,
        }
        self.json_kwargs |= json_kwargs
        super().__init__(content, status_code, headers)

    async def serialize_content(self, content: Any) -> bytes:
        return json.dumps(content, **self.json_kwargs).encode(self.charset)


class Headers(Mapping[str, str]):
    __slots__ = ("_dict",)

    def __init__(self, headers: Optional[Union[Mapping[str, str], Iterable[Tuple[str, str]]]] = None) -> None:
        store: Dict[str, str] = {}
        if isinstance(headers, Mapping):
            items = headers.items()
        elif headers is None:
            items = ()
        else:
            items = headers
        for key, value in items:
            key = key.lower()
            if key in store:
                store[key] = f"{store[key]}, {value}"
            else:
                store[key] = value

        self._dict = store

    def __getitem__(self, key: str) -> str:
        return self._dict[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)


class MutableHeaders(Headers):
    __slots__ = Headers.__slots__

    def __setitem__(self, key: str, value: str) -> None:
        self._dict[key.lower()] = value

    def __delitem__(self, key: str) -> None:
        del self._dict[key.lower()]

    def append(self, key: str, value: str) -> None:
        key = key.lower()
        if key in self._dict:
            self._dict[key] = f"{self._dict[key]}, {value}"
        else:
            self._dict[key] = value
