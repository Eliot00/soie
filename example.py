from soie.applications import Soie
from soie.responses import Response
from soie.routing import Router

router = Router()


@router.http.get("/")
async def homepage(request) -> Response:
    return Response("Hello, world!")


@router.http.get("/cat")
async def cat(request) -> Response:
    return Response("Meow!")


app = Soie(router=router)
