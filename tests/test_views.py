import pytest

from soie.responses import JSONResponse
from soie.views import auto_json_response


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
