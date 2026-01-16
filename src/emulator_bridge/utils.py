from datetime import datetime
from logging import getLogger

__all__ = ["now", "log"]


def now():
    return datetime.now().astimezone().replace(microsecond=0)


log = getLogger("uvicorn.error.app")
