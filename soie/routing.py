from __future__ import annotations

import dataclasses
import os
from typing import Callable, Collection, Iterable, Iterator, List, Optional, cast

from .exceptions import HTTPException
from .views import AllowMethod, View, require_http_method


class Router:
    def __init__(self, routes: Iterable[BaseRoute] = None) -> None:
        if routes is None:
            self._routes = []
        else:
            self._routes = list(routes)
        self.root = RadixTreeNode("/")

    @property
    def http(self) -> HTTPRouteRegister:
        return HTTPRouteRegister(self)

    def add_route(self, route: BaseRoute) -> Router:
        if self.search(route.path) is not None:
            raise ValueError(f"This constant route {route.path} can be matched by the added routes.")
        new_node = insert_node(self.root, route.path[1:])
        new_node.handler = route.endpoint
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
            if not path.startswith(node.characters):
                continue
            length = len(node.characters)
            if length == len(path):
                return node.handler
            path = path[length:]
            for child in node.children or ():
                stack.append((path, child))
        return None

    def __iter__(self) -> Iterator[BaseRoute]:
        return iter(self._routes)


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


@dataclasses.dataclass
class RadixTreeNode:
    characters: str
    handler: Optional[View] = None
    children: Optional[List[RadixTreeNode]] = None


def insert_node(node: RadixTreeNode, path: str) -> RadixTreeNode:
    if path == "":
        return node
    if node.children is None:
        node.children = []
    for child in node.children:
        common_prefix = os.path.commonprefix([child.characters, path])
        if common_prefix == "":
            continue
        if child.characters == common_prefix:
            return insert_node(child, path[len(common_prefix) :])
        child_index = node.children.index(child)
        prefix_node = RadixTreeNode(common_prefix, children=[])
        node.children[child_index] = prefix_node
        child.characters = child.characters[len(common_prefix) :]
        cast(List[RadixTreeNode], prefix_node.children).insert(0, child)
        new_node = RadixTreeNode(path[len(common_prefix) :])
        cast(List[RadixTreeNode], prefix_node.children).insert(0, new_node)
        return new_node
    new_node = RadixTreeNode(path)
    node.children.insert(0, new_node)
    return new_node
