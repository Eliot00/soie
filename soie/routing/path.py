import re
from typing import Any, Dict, Protocol, Tuple


class ParamConvertor(Protocol):
    regex: str

    def to_python(self, value: str) -> Any:
        ...


class StringConvertor:
    regex = "[^/]+"

    def to_python(self, value: str) -> str:
        return value


class IntegerConvertor:
    regex = "[0-9]+"

    def to_python(self, value: str) -> int:
        return int(value)


PARAM_REGEX = re.compile(r"{([^\d]\w*)(:\w+)?}")
CONVERTORS = {"str": StringConvertor(), "int": IntegerConvertor()}


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
