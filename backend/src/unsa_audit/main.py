"""Composition root: unico lugar donde se conectan puertos con adaptadores."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from unsa_audit.core.config import Settings, get_settings
from unsa_audit.core.database import create_engine
from unsa_audit.health.application.check_health import CheckHealth, DatabaseProbe
from unsa_audit.health.infrastructure.sqlalchemy_probe import SqlAlchemyDatabaseProbe
from unsa_audit.health.interface.router import router as health_router


def create_app(
    settings: Settings | None = None,
    probe: DatabaseProbe | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    engine: AsyncEngine | None = None
    if probe is None:
        engine = create_engine(settings.database_url)
        probe = SqlAlchemyDatabaseProbe(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if engine is not None:
            await engine.dispose()

    app = FastAPI(title="UNSA Audit Capacitator (POC)", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = settings
    app.state.check_health = CheckHealth(probe)
    app.include_router(health_router)
    return app


def run() -> None:
    uvicorn.run("unsa_audit.main:app", host="0.0.0.0", port=8000, reload=False)


def __getattr__(name: str) -> FastAPI:
    # `uvicorn unsa_audit.main:app` crea la app de forma perezosa.
    if name == "app":
        return create_app()
    raise AttributeError(name)
