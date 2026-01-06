from fastapi import APIRouter, Request
from scalar_fastapi import get_scalar_api_reference

router = APIRouter(tags=["Docs"])


@router.get("/scalar", include_in_schema=False)
async def scalar_html(req: Request):
    return get_scalar_api_reference(
        openapi_url=req.app.openapi_url, title="Emulator Bridge"
    )
