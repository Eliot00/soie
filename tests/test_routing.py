import pytest

from soie.exceptions import ParamNotMatched
from soie.requests import Request
from soie.responses import PlainTextResponse
from soie.routing import Route, Router
from soie.routing.routes import IntegerConvertor, RawConvertor, compile_path


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


@pytest.mark.parametrize(
    "convertor,path",
    [
        (RawConvertor(), "/error"),
        (IntegerConvertor(), "nan"),
    ],
)
def test_builtin_params_convertor_not_matched(convertor, path):
    with pytest.raises(ParamNotMatched):
        convertor.match(path)


@pytest.mark.parametrize(
    "path,real_path,params",
    [
        ("/hello", "/hello", {}),
        ("/hi/{name}", "/hi/Jack", {"name": "Jack"}),
        ("/order/{id:int}", "/order/123", {"id": 123}),
        ("/archives/file.{suffix}", "/archives/file.jpg", {"suffix": "jpg"}),
    ],
)
def test_router_inject_params_to_request(path, real_path, params):
    request = FakeRequest(real_path)
    router = Router().add_route(Route(path, fake_view))

    router.search(request)

    assert request.path_params == params


def test_dynamic_path_search():
    static_route = Route("/project/top", fake_view)
    dynamic_route = Route("/project/{id:int}", fake_view)

    router = Router().add_route(static_route).add_route(dynamic_route)

    assert router.search(FakeRequest("/project/top")) is static_route
    assert router.search(FakeRequest("/project/12")) is dynamic_route
    assert router.search(FakeRequest("/project/another")) is None


async def fake_view(request):
    return PlainTextResponse()


class FakeRequest(Request):
    def __init__(self, path: str) -> None:
        self._scope = {"path": path}
