from __future__ import annotations

import dataclasses
import os
import re
from typing import Callable, Collection, Dict, Iterable, List, Optional, cast

from ..exceptions import HTTPException, ParamNotMatched
from ..views import AllowMethod, View, require_http_method
from .routes import ParamConvertor, Route


class Router:
    def __init__(self, routes: Iterable[Route] = ()) -> None:
        self.root = RadixTreeNode("/")
        for route in routes:
            self.add_route(route)

    @property
    def http(self) -> HTTPRouteRegister:
        return HTTPRouteRegister(self)

    def add_route(self, route: Route) -> Router:
        compiled_path, param_convertors = route.compiled_path, route.param_convertors
        node = insert_node(self.root, compiled_path[1:], param_convertors)
        if node.route is not None:
            raise ValueError(f"Handler are already registered for path '{compiled_path}'.")
        node.route = route
        return self

    def get_route(self, path: str) -> Route:
        route = self.search(path)
        if route is None:
            raise HTTPException(404)
        return route

    def search(self, path: str) -> Optional[Route]:
        stack = [(path, self.root)]
        params = {}
        while stack:
            path, node = stack.pop()
            if node.convertor is None:
                if not path.startswith(node.characters):
                    continue
                length = len(node.characters)
            else:
                try:
                    matched_var = node.convertor.match(path)
                except ParamNotMatched:
                    continue
                length = len(matched_var)
                params[node.characters] = matched_var
            if length == len(path):
                return Route.inject_path_params(node.route, params)
            path = path[length:]
            for child in node.children or ():
                stack.append((path, child))
        return None


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
            route = Route(path, wrapped_endpoint)
            self._router.add_route(route)
            return wrapped_endpoint

        return register


# from https://github.com/index-py/index.py/blob/master/indexpy/routing/tree.py
@dataclasses.dataclass
class RadixTreeNode:
    characters: str
    convertor: Optional[ParamConvertor] = None
    route: Optional[Route] = None
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
        param_children = (child for child in node.children if child.convertor is not None)
        for child in param_children:
            if (child.convertor.__class__ is convertor.__class__) != (child.characters == param_name):
                raise ValueError(
                    "The same regular matching is used in the same position, but the parameter names are different"
                )
            if child.characters == param_name:
                return insert_node(child, path[length:], param_convertors)

        new_node = RadixTreeNode(param_name, convertor=convertor)
        node.children.insert(0, new_node)
        return insert_node(new_node, path[length:], param_convertors)
    else:
        length = path.find("{")
        if length == -1:
            length = len(path)

        static_children = (child for child in node.children if child.convertor is None)
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
