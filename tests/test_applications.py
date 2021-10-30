import pytest
from async_asgi_testclient import TestClient

from soie.applications import Soie
from soie.responses import JSONResponse, PlainTextResponse


@pytest.mark.asyncio
async def test_dynamic_router_app():
    app = Soie()

    @app.router.http.get("/hi/{name}")
    async def greet(request):
        params = request["path_params"]
        return JSONResponse(params)

    async with TestClient(app) as client:
        res = await client.get("/hi/Jack")
        assert res.json() == {"name": "Jack"}


@pytest.mark.asyncio
async def test_add_exception_handler():
    app = Soie()

    @app.exception_handler(ValueError)
    async def error_handler(exc):
        return PlainTextResponse(str(exc), 500)

    @app.router.http.get("/value_error")
    async def value_error(request):
        raise ValueError("value error")

    @app.router.http.get("/no_catch")
    async def no_catch(request):
        raise AttributeError("attribute error")

    async with TestClient(app) as client:
        res = await client.get("/value_error")
        assert res.status_code == 500
        assert res.text == "value error"

        not_found = await client.get("/not_found")
        assert not_found.status_code == 404

        with pytest.raises(AttributeError):
            await client.get("/no_catch")
