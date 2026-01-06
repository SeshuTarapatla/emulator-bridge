import asyncio

from adbutils import adb
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from emulator_bridge.controllers.lease import lease_manager
from emulator_bridge.utils import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting adb server")
    adb.make_connection()
    log.info("Starting lease manager")
    lease_manager_task = asyncio.create_task(lease_manager())
    try:
        yield
    finally:
        lease_manager_task.cancel()
