import pytest
from async_asgi_testclient import TestClient

from soie.responses import JSONResponse


@pytest.mark.asyncio
async def test_json_none_response():
    async def app(scope, receive, send):
        response = JSONResponse(None)
        await response(scope, receive, send)

    async with TestClient(app) as client:
        response = await client.get("/")
        assert response.json() is None
