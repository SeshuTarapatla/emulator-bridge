from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from emulator_bridge.controllers.lease import LEASE_STATUS
from emulator_bridge.utils import now

DEFAULT_LEASE_DURATION = 180  # 3 minutes
DEV_MODE_DURATIION = timedelta(days=1)  # 1 day


class LeaseInfo(BaseModel):
    id: str = Field(pattern=r"^lease-[0-9a-z]{8}")
    position: int = Field(ge=-1)
    start_at: datetime | None = None
    end_at: datetime | None = None
    duration: timedelta
    status: LEASE_STATUS

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "lease-xxxxyyyy",
                "position": 1,
                "start_at": str(now()),
                "end_at": str(now() + timedelta(seconds=180)),
                "duration": "PT3M",
                "status": "queued",
            }
        }
    }


class LeaseRequest(BaseModel):
    duration: int = Field(gt=0, default=DEFAULT_LEASE_DURATION)
