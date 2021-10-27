import pytest

from soie.responses import PlainTextResponse
from soie.routing import HTTPRoute, Router
from soie.routing.path import compile_path


@pytest.mark.parametrize(
    "raw,expect",
    [
        ("/path", "/path"),
        ("/hello/{name}", "/hello/{name}"),
        ("/hello/{name:str}", "/hello/{name}"),
        ("/student/{name:str}/{age:int}", "/student/{name}/{age}"),
    ],
)
def test_compile_path(raw, expect):
    compiled_path, _ = compile_path(raw)
    assert compiled_path == expect


def test_dynamic_path_search():
    async def fake_view(request):
        return PlainTextResponse()

    static_route = HTTPRoute("/project/top", fake_view)
    dynamic_route = HTTPRoute("/project/{id:int}", fake_view)

    router = Router().add_route(static_route).add_route(dynamic_route)

    assert router.search("/project/top") is not None
    assert router.search("/project/12") is not None
    assert router.search("/project/another") is None
