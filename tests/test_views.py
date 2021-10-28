from soie.responses import PlainTextResponse
from soie.views import inject_path_params


def test_inject_wrap():
    params = (("number", i) for i in range(5))

    async def one(request):
        return PlainTextResponse()

    async def two(request):
        return PlainTextResponse()

    async def three(request):
        return PlainTextResponse()

    async def four(request):
        return PlainTextResponse()

    async def five(request):
        return PlainTextResponse()

    assert inject_path_params(params, one).__name__ == "one"
    assert inject_path_params(params, two).__name__ == "two"
    assert inject_path_params(params, three).__name__ == "three"
    assert inject_path_params(params, four).__name__ == "four"
    assert inject_path_params(params, five).__name__ == "five"
