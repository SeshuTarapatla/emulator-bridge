import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Request, Response
from fastapi.responses import StreamingResponse

from emulator_bridge.controllers.emulator import Emulator
from emulator_bridge.controllers.lease import (
    EMULATOR_SWITCH,
    Lease,
    lease_queue,
)
from emulator_bridge.models.emulator import DEV_MODE_DURATIION, LeaseInfo, LeaseRequest
from emulator_bridge.utils import now


def lease_info_response(lease: Lease, include_dates: bool = False) -> LeaseInfo:
    lease_info = LeaseInfo(
        id=lease.id,
        position=lease.position,
        duration=lease.duration,
        status=lease.status,
    )
    if include_dates and lease.status != "queued":
        lease_info.start_at = lease.start_at
        lease_info.end_at = lease.end_at
    return lease_info


async def stream_lease_status(request: Request, lease: Lease):
    while True:
        yield f"data: status: {lease.status} | position: {lease.position}\n\n"
        if await request.is_disconnected():
            return
        await asyncio.sleep(1)


router = APIRouter(tags=["Emulator"])


@router.get(
    "/lease",
    status_code=200,
    response_model=list[LeaseInfo],
    response_model_exclude_none=True,
)
async def list_lease_queue():
    return [lease_info_response(lease) for lease in lease_queue]


@router.delete("/lease", status_code=200)
async def clear_lease_queue(bg: BackgroundTasks):
    await lease_queue.clear()
    bg.add_task(
        asyncio.run, Emulator.stop(lease_queue.pid)
    ) if EMULATOR_SWITCH else None
    return Response(status_code=200)


@router.post(
    "/lease",
    status_code=200,
    response_model=LeaseInfo,
    response_model_exclude_none=True,
)
async def request_lease(
    request: LeaseRequest = LeaseRequest(),
) -> LeaseInfo:
    lease = await lease_queue.new(request.duration)
    return lease_info_response(lease)


@router.post("/lease/dev", status_code=200, response_model=LeaseInfo)
async def emulator_in_dev_mode():
    lease = await lease_queue.new(int(DEV_MODE_DURATIION.total_seconds()))
    return lease_info_response(lease)


@router.get("/{id}", status_code=200, response_model=LeaseInfo)
async def lease_info(id: str = Path(pattern=r"^lease-[0-9a-z]{8}")):
    lease = await lease_queue.query(id)
    if lease:
        return lease_info_response(lease, include_dates=True)
    raise HTTPException(status_code=404, detail=f"{id} not found")


@router.post("/{id}/complete", status_code=200, response_model=LeaseInfo)
async def complete_lease(id: str = Path(pattern=r"^lease-[0-9a-z]{8}")):
    lease = await lease_queue.query(id)
    if lease:
        lease.complete()
        return lease_info_response(lease, include_dates=True)
    raise HTTPException(status_code=404, detail=f"{id} not found")


@router.post("/{id}/ping", status_code=200, response_model=LeaseInfo)
async def keep_lease_alive(
    id: str = Path(pattern=r"^lease-[0-9a-z]{8}"),
):
    lease = await lease_queue.query(id)
    if lease:
        lease.end_at = now() + lease.duration
        lease.duration = lease.end_at - lease.start_at
        return lease_info_response(lease, include_dates=True)
    raise HTTPException(status_code=404, detail=f"{id} not found")


@router.get("/{id}/status", status_code=200)
async def lease_live_status(
    request: Request, id: str = Path(pattern=r"^lease-[0-9a-z]{8}")
):
    lease = await lease_queue.query(id)
    if lease:
        return StreamingResponse(
            stream_lease_status(request, lease),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    raise HTTPException(status_code=404, detail=f"{id} not found")
