import pytest
from async_asgi_testclient import TestClient


@pytest.mark.asyncio
async def test_simple_app():
    from example import app

    async with TestClient(app) as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert res.text == "Hello, world!"

        res = await client.get("/cat")
        assert res.status_code == 200
        assert res.text == "Meow!"

        res = await client.post("/cat")
        assert res.status_code == 405

        res = await client.get("/utopia")
        assert res.status_code == 404
