import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db.models import Project, Service
from app.models.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.services import project as svc

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[Project]:
    return await svc.list_projects(db)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Project:
    project = await svc.create_project(db, payload)
    logger.info("project created", project_id=project.id, name=project.name)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> Project:
    project = await svc.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)
) -> Project:
    project = await svc.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return await svc.update_project(db, project, payload)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)) -> None:
    project = await svc.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await svc.delete_project(db, project)


@router.post("/{project_id}/services", response_model=ServiceResponse, status_code=201)
async def create_service(
    project_id: str, payload: ServiceCreate, db: AsyncSession = Depends(get_db)
) -> Service:
    project = await svc.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    service = await svc.create_service(db, project_id, payload)
    logger.info("service created", service_id=service.id, project_id=project_id)
    return service


@router.get("/{project_id}/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    project_id: str, service_id: str, db: AsyncSession = Depends(get_db)
) -> Service:
    service = await svc.get_service(db, project_id, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.patch("/{project_id}/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    project_id: str,
    service_id: str,
    payload: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Service:
    service = await svc.get_service(db, project_id, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return await svc.update_service(db, service, payload)


@router.delete("/{project_id}/services/{service_id}", status_code=204)
async def delete_service(
    project_id: str, service_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    service = await svc.get_service(db, project_id, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    await svc.delete_service(db, service)
