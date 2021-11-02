import pytest

from soie.responses import JSONResponse, PlainTextResponse
from soie.views import auto_json_response, inject_path_params


def test_inject_wrap():
    params = (("number", i) for i in range(5))

    async def one(_):
        return PlainTextResponse()

    async def two(_):
        return PlainTextResponse()

    async def three(_):
        return PlainTextResponse()

    async def four(_):
        return PlainTextResponse()

    async def five(_):
        return PlainTextResponse()

    assert inject_path_params(params, one).__name__ == "one"
    assert inject_path_params(params, two).__name__ == "two"
    assert inject_path_params(params, three).__name__ == "three"
    assert inject_path_params(params, four).__name__ == "four"
    assert inject_path_params(params, five).__name__ == "five"


@pytest.mark.asyncio
async def test_auto_json_response():
    @auto_json_response
    async def handle_dict(_):
        return {"hello": "world"}

    res = await handle_dict(None)  # type: ignore
    assert isinstance(res, JSONResponse)
    assert res.content == {"hello": "world"}

    @auto_json_response
    async def handle_str(_):
        return "hello world"

    res = await handle_str(None)  # type: ignore
    assert isinstance(res, JSONResponse)
    assert res.content == "hello world"

    @auto_json_response
    async def handle_int(_):
        return 200

    res = await handle_int(None)  # type: ignore
    assert isinstance(res, JSONResponse)
    assert res.content == 200
