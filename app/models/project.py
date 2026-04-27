from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Host = Literal[
    "GitHub", "Cloudflare", "DigitalOcean", "Vercel", "Netlify",
    "Render", "Railway", "Fly.io", "AWS", "GCP", "Azure", "Alibaba", "Other",
]
Status = Literal["operational", "outage"]


class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1)
    host: Host
    url: str = Field(..., min_length=1)
    repo_url: str | None = None
    status: Status = "operational"


class ServiceUpdate(BaseModel):
    name: str | None = None
    host: Host | None = None
    url: str | None = None
    repo_url: str | None = None
    status: Status | None = None


class ServiceResponse(BaseModel):
    id: str
    project_id: str
    name: str
    host: str
    url: str
    repo_url: str | None = None
    status: str
    last_checked: datetime | None = None

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    services: list[ServiceCreate] = []


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    services: list[ServiceResponse] = []

    model_config = {"from_attributes": True}
