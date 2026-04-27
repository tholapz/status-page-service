import asyncio
from datetime import datetime, timezone

import httpx
import structlog
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.db.models import Service

logger = structlog.get_logger(__name__)


async def _probe(client: httpx.AsyncClient, service: Service) -> str:
    try:
        response = await client.get(service.url, timeout=10.0, follow_redirects=True)
        return "operational" if response.is_success else "outage"
    except Exception:
        return "outage"


async def _check_and_update(client: httpx.AsyncClient, service: Service) -> None:
    status = await _probe(client, service)
    async with AsyncSessionLocal() as db:
        svc = await db.get(Service, service.id)
        if svc is not None:
            svc.status = status
            svc.last_checked = datetime.now(timezone.utc)
            await db.commit()
    logger.info("service checked", service_id=service.id, url=service.url, status=status)


async def run_checks() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Service))
        services = list(result.scalars().all())

    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            *[_check_and_update(client, svc) for svc in services],
            return_exceptions=True,
        )


async def checker_loop() -> None:
    while True:
        try:
            await run_checks()
        except Exception as exc:
            logger.error("checker run failed", error=str(exc))
        await asyncio.sleep(settings.check_interval_seconds)
