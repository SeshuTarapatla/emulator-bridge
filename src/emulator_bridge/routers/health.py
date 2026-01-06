from fastapi import APIRouter, Response

router = APIRouter(tags=["Health"])


@router.get("/", status_code=200)
async def server_status():
    return Response(status_code=200)
