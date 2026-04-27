import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Service
from app.models.project import ProjectCreate, ProjectUpdate, ServiceCreate, ServiceUpdate


async def list_projects(db: AsyncSession) -> list[Project]:
    result = await db.execute(select(Project))
    return list(result.scalars().all())


async def get_project(db: AsyncSession, project_id: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, payload: ProjectCreate) -> Project:
    project = Project(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
    )
    for svc in payload.services:
        project.services.append(
            Service(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name=svc.name,
                host=svc.host,
                url=svc.url,
                repo_url=svc.repo_url,
                status=svc.status,
            )
        )
    db.add(project)
    await db.commit()
    return project


async def update_project(db: AsyncSession, project: Project, payload: ProjectUpdate) -> Project:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    await db.commit()
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    await db.delete(project)
    await db.commit()


async def get_service(db: AsyncSession, project_id: str, service_id: str) -> Service | None:
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.project_id == project_id)
    )
    return result.scalar_one_or_none()


async def create_service(db: AsyncSession, project_id: str, payload: ServiceCreate) -> Service:
    service = Service(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=payload.name,
        host=payload.host,
        url=payload.url,
        repo_url=payload.repo_url,
        status=payload.status,
    )
    db.add(service)
    await db.commit()
    return service


async def update_service(db: AsyncSession, service: Service, payload: ServiceUpdate) -> Service:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    await db.commit()
    return service


async def delete_service(db: AsyncSession, service: Service) -> None:
    await db.delete(service)
    await db.commit()
