from soie.applications import Soie
from soie.responses import PlainTextResponse
from soie.routing import Router

router = Router()


@router.http.get("/")
async def homepage(request) -> PlainTextResponse:
    return PlainTextResponse("Hello, world!")


@router.http.get("/cat")
async def cat(request) -> PlainTextResponse:
    return PlainTextResponse("Meow!")


app = Soie(router=router)
