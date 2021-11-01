from __future__ import annotations

from http import HTTPStatus
from typing import Mapping, Optional

from .responses import JSONResponse, Response


class SoieException(Exception):
    """Base Error"""

    pass


class HTTPException(SoieException):
    def __init__(
        self,
        status_code: int = 400,
        headers: Optional[Mapping[str, str]] = None,
        message: Optional[str | dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        if message is None:
            message = HTTPStatus(status_code).description
        self.message = message
        super().__init__(status_code, message)


async def http_exception_to_response(_, exc: HTTPException) -> Response:
    return JSONResponse(content=exc.message, status_code=exc.status_code, headers=exc.headers)


class ParamNotMatched(SoieException):
    pass
