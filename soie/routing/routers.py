from __future__ import annotations

import dataclasses
import os
import re
from typing import Callable, Collection, Dict, Iterable, List, Optional, Pattern, cast

from ..exceptions import HTTPException
from ..views import AllowMethod, View, require_http_method
from .path import ParamConvertor, compile_path


class Router:
    def __init__(self, routes: Iterable[BaseRoute] = ()) -> None:
        self.root = RadixTreeNode("/")
        for route in routes:
            self.add_route(route)

    @property
    def http(self) -> HTTPRouteRegister:
        return HTTPRouteRegister(self)

    def add_route(self, route: BaseRoute) -> Router:
        format_path, param_convertors = compile_path(route.path)
        node = insert_node(self.root, format_path[1:], param_convertors)
        if node.handler is not None:
            raise ValueError(f"Handler are already registered for path '{format_path}'.")
        node.handler = route.endpoint
        return self

    def get_endpoint(self, path: str) -> View:
        endpoint = self.search(path)
        if endpoint is None:
            raise HTTPException(404)
        return endpoint

    def search(self, path: str) -> Optional[View]:
        stack = [(path, self.root)]
        while stack:
            path, node = stack.pop()
            if node.re_pattern is None:
                if not path.startswith(node.characters):
                    continue
                length = len(node.characters)
            else:
                match = re.match(node.re_pattern, path)
                if match is None:
                    continue
                result = match.group()
                length = len(result)
            if length == len(path):
                return node.handler
            path = path[length:]
            for child in node.children or ():
                stack.append((path, child))
        return None


@dataclasses.dataclass
class BaseRoute:
    path: str
    endpoint: View

    def __post_init__(self) -> None:
        assert self.path.startswith("/"), "Route path must start with '/'"


@dataclasses.dataclass
class HTTPRoute(BaseRoute):
    pass


class HTTPRouteRegister:
    def __init__(self, router: Router) -> None:
        self._router = router

    def get(self, path: str) -> Callable[[View], View]:
        return self._register_with_method(("GET",), path)

    def post(self, path: str) -> Callable[[View], View]:
        return self._register_with_method(("POST",), path)

    def put(self, path: str) -> Callable[[View], View]:
        return self._register_with_method(("PUT",), path)

    def patch(self, path: str) -> Callable[[View], View]:
        return self._register_with_method(("PATCH",), path)

    def delete(self, path: str) -> Callable[[View], View]:
        return self._register_with_method(("DELETE",), path)

    def any(self, path: str) -> Callable[[View], View]:
        return self._register_with_method(
            (
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            ),
            path,
        )

    def _register_with_method(self, methods: Collection[AllowMethod], path: str) -> Callable[[View], View]:
        def register(endpoint: View) -> View:
            wrapped_endpoint = require_http_method(methods)(endpoint)
            route = HTTPRoute(path, wrapped_endpoint)
            self._router.add_route(route)
            return wrapped_endpoint

        return register


# from https://github.com/index-py/index.py/blob/master/indexpy/routing/tree.py
@dataclasses.dataclass
class RadixTreeNode:
    characters: str
    re_pattern: Optional[Pattern] = None
    handler: Optional[View] = None
    children: Optional[List[RadixTreeNode]] = None


def insert_node(node: RadixTreeNode, path: str, param_convertors: Dict[str, ParamConvertor]) -> RadixTreeNode:
    if path == "":
        return node
    if node.children is None:
        node.children = []

    matched = re.match(r"^{\w+}", path)

    if matched is not None:
        length = matched.end()
        param_name = path[1 : length - 1]
        convertor = param_convertors[param_name]
        re_pattern = re.compile(convertor.regex)
        regex_children = (child for child in node.children if child.re_pattern is not None)
        for child in regex_children:
            if (child.re_pattern == re_pattern) != (child.characters == param_name):
                raise ValueError(
                    "The same regular matching is used in the same position, but the parameter names are different"
                )
            if child.characters == param_name:
                return insert_node(child, path[length:], param_convertors)

        new_node = RadixTreeNode(param_name, re_pattern=re_pattern)
        node.children.insert(0, new_node)
        return insert_node(new_node, path[length:], param_convertors)
    else:
        length = path.find("{")
        if length == -1:
            length = len(path)

        static_children = (child for child in node.children if child.re_pattern is None)
        for child in static_children:
            common_prefix = os.path.commonprefix([child.characters, path[:length]])
            if common_prefix == "":
                continue
            if child.characters == common_prefix:
                return insert_node(child, path[len(common_prefix) :], param_convertors)
            child_index = node.children.index(child)
            prefix_node = RadixTreeNode(common_prefix, children=[])
            node.children[child_index] = prefix_node
            child.characters = child.characters[len(common_prefix) :]
            cast(List[RadixTreeNode], prefix_node.children).insert(0, child)
            if path[:length] == common_prefix:
                return insert_node(prefix_node, path[length:], param_convertors)

            new_node = RadixTreeNode(path[len(common_prefix) : length])
            cast(List[RadixTreeNode], prefix_node.children).insert(0, new_node)
            return insert_node(new_node, path[length:], param_convertors)

        new_node = RadixTreeNode(path[:length])
        node.children.insert(0, new_node)
        return insert_node(new_node, path[length:], param_convertors)
