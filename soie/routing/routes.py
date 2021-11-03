from __future__ import annotations

import re
from typing import Any, Dict, Protocol, Tuple

from ..exceptions import ParamNotMatched
from ..views import View


class Route:
    def __init__(self, path: str, endpoint: View) -> None:
        assert path.startswith("/") and not path.endswith("/"), "Route path must start with '/' and not end with '/'."

        self.path = path
        self.endpoint = endpoint
        self.compiled_path, self.param_convertors = compile_path(path)


class ParamConvertor(Protocol):
    def match(self, path: str) -> str:
        ...

    def to_python(self, value: str) -> Any:
        ...


class RawConvertor:
    regex = re.compile("[^/]+")

    def match(self, path: str) -> str:
        try:
            return re.match(self.regex, path).group()
        except AttributeError:
            raise ParamNotMatched()

    def to_python(self, value: str) -> str:
        return value


class IntegerConvertor(RawConvertor):
    regex = re.compile("[0-9]+")

    def to_python(self, value: str) -> int:
        return int(value)


PARAM_REGEX = re.compile(r"{([^\d]\w*)(:\w+)?}")
CONVERTORS = {"str": RawConvertor(), "int": IntegerConvertor()}


def compile_path(path: str) -> Tuple[str, Dict[str, ParamConvertor]]:
    format_path = ""
    idx = 0
    param_convertors = {}
    for match in PARAM_REGEX.finditer(path):
        param_name, convertor_name = match.groups(default="str")
        convertor_name = convertor_name.lstrip(":")
        if convertor_name not in CONVERTORS:
            raise ValueError(f"Unknown path param convertor '{convertor_name}'")
        convertor = CONVERTORS[convertor_name]

        format_path += path[idx : match.start()]
        format_path += "{" + param_name + "}"
        param_convertors[param_name] = convertor

        idx = match.end()

    format_path += path[idx:]
    return format_path, param_convertors
