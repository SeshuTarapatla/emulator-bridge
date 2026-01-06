import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from secrets import token_hex
from typing import Literal

from emulator_bridge.controllers.emulator import Emulator
from emulator_bridge.utils import log, now

__all__ = ["lease_queue"]

EMULATOR_SWITCH: bool = True


@dataclass
class Lease:
    id: str
    position: int
    start_at: datetime
    end_at: datetime
    duration: timedelta
    status: Literal["queued", "active", "expired", "completed"]

    def __init__(self, duration: int, position: int):
        self.id = f"lease-{token_hex(8)[:8]}"
        self.position = position
        self.duration = timedelta(seconds=duration)
        self.start_at = now()
        self.end_at = self.start_at + self.duration
        self.status = "queued"

    def start(self):
        self.start_at = now()
        self.end_at = self.start_at + self.duration
        self.status = "active"
        log.info(f"{self.id} | Lease Active   | Ends at: {self.end_at}")

    async def _stop(self):
        self.end_at = now()
        self.duration = self.end_at - self.start_at
        self.position = -1

    async def complete(self):
        await self._stop()
        self.status = "completed"
        log.info(f"{self.id} | Lease Complete | Total Duration: {self.duration}")

    async def expire(self):
        await self._stop()
        self.status = "expired"
        log.info(f"{self.id} | Lease Expired  | Total Duration: {self.duration}")


class LeaseQueue(deque[Lease]):
    def __init__(self):
        super().__init__()
        self.lock = asyncio.Lock()
        self.entries: dict[str, Lease] = {}

    async def new(self, duration: int) -> Lease:
        async with self.lock:
            lease = Lease(duration, len(self))
            self.append(lease)
            log.info(f"{lease.id} | Lease Added    | Position: {lease.position} | Duration: {lease.duration}")
            return lease

    async def next(self):
        async with self.lock:
            if self:
                lease = super().popleft()
                self.entries[lease.id] = lease
                for lease in self:
                    lease.position -= 1

    async def query(self, id: str) -> Lease | None:
        for entry in self:
            if entry.id == id:
                return entry
        if id in self.entries:
            return self.entries[id]

    @property
    async def current(self) -> Lease | None:
        async with self.lock:
            return self[0] if self else None


lease_queue = LeaseQueue()


async def lease_manager():
    while True:
        if lease := await lease_queue.current:
            if lease.status == "queued":
                log.info(f"{lease.id} | Starting Emulator")
                await Emulator.start() if EMULATOR_SWITCH else None
                lease.start()
            if now() >= lease.end_at:
                if lease.status != "completed":
                    await lease.expire()
                await lease_queue.next()
                log.info(f"{lease.id} | Stopping Emulator")
                await Emulator.stop() if EMULATOR_SWITCH else None
        await asyncio.sleep(1)
