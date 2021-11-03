import pytest
from async_asgi_testclient import TestClient

from soie.applications import Soie
from soie.responses import PlainTextResponse


@pytest.mark.asyncio
async def test_add_exception_handler():
    app = Soie()

    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return PlainTextResponse(str(exc), 500)

    @app.exception_handler(KeyError)
    async def key_error_handler(request, exc):
        return PlainTextResponse(request.query_params["key"], 422)

    @app.router.http.get("/value_error")  # type: ignore
    async def value_error(request):
        raise ValueError("value error")

    @app.router.http.get("/key_error")
    async def key_error(request):
        request.query_params["error_key"]
        return PlainTextResponse()

    @app.router.http.get("/no_catch")  # type: ignore
    async def no_catch(request):
        raise AttributeError("attribute error")

    async with TestClient(app) as client:
        res = await client.get("/value_error")
        assert res.status_code == 500
        assert res.text == "value error"

        key_res = await client.get("/key_error?key=soie")
        assert key_res.status_code == 422
        assert key_res.text == "soie"

        not_found = await client.get("/not_found")
        assert not_found.status_code == 404

        with pytest.raises(AttributeError):
            await client.get("/no_catch")
