import uvicorn
from fastapi import FastAPI

from emulator_bridge.controllers.lifespan import lifespan
from emulator_bridge.routers import docs, health, lease

app = FastAPI(lifespan=lifespan)
app.include_router(lease.router)
app.include_router(health.router)
app.include_router(docs.router)


def main(dev: bool = False) -> None:
    if dev:
        uvicorn.run("emulator_bridge.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
