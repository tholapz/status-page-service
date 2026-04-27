import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal, engine
from app.db.models import Base, Project, Service
from app.middleware import RequestIDMiddleware, add_cors_middleware
from app.routers import health
from app.routers.v1 import projects as v1_projects
from app.services.checker import checker_loop
from app.utils.logging import configure_logging

configure_logging()

logger = structlog.get_logger(__name__)

_PROJECTS_JSON = Path(__file__).parent.parent / "projects.json"


async def _seed_database() -> None:
    if not _PROJECTS_JSON.exists():
        return
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Project))
        if existing.scalars().first() is not None:
            return
        data: list[dict[str, object]] = json.loads(_PROJECTS_JSON.read_text())
        for p in data:
            project = Project(
                id=str(p["id"]),
                name=str(p["name"]),
                description=str(p["description"]) if p.get("description") else None,
            )
            for s in p.get("services", []):  # type: ignore[union-attr]
                assert isinstance(s, dict)
                project.services.append(
                    Service(
                        id=str(s["id"]),
                        project_id=project.id,
                        name=str(s["name"]),
                        host=str(s["host"]),
                        url=str(s["url"]),
                        repo_url=str(s["repo_url"]) if s.get("repo_url") else None,
                        status=str(s.get("status", "operational")),
                    )
                )
            db.add(project)
        await db.commit()
        logger.info("database seeded", source=str(_PROJECTS_JSON), count=len(data))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _seed_database()

    checker_task = asyncio.create_task(checker_loop())
    logger.info(
        "service starting",
        app_name=settings.app_name,
        environment=settings.environment,
        port=settings.port,
    )
    yield
    checker_task.cancel()
    try:
        await checker_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        redirect_slashes=False,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )

    app.add_middleware(RequestIDMiddleware)
    add_cors_middleware(app)

    app.include_router(health.router)
    app.include_router(v1_projects.router, prefix="/api/v1")

    return app


app = create_app()
