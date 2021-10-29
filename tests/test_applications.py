import pytest
from async_asgi_testclient import TestClient

from soie.applications import Soie
from soie.responses import JSONResponse


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
