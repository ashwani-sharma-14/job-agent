from datetime import datetime
from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    source_url: str | None = None


class JobCreate(JobBase):
    job_description: str | None = None


class JobResponse(JobBase):
    id: str
    match_score: float | None = None
    required_skills: str | None = None
    missing_skills: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class JobAnalysis(BaseModel):
    match_score: float
    required_skills: list[str]
    missing_skills: list[str]
    recommendation: str | None = None


class ApplicationCreate(BaseModel):
    job_id: str
    resume_path: str | None = None
    cover_letter: str | None = None
    status: str = "generated"


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    status: str
    cover_letter: str | None = None
    applied_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResumeContext(BaseModel):
    name: str | None = None
    skills: list[str] = []
    technologies: list[str] = []
    experience: list[str] = []
    projects: list[str] = []
    preferred_roles: list[str] = []


class PipelineResult(BaseModel):
    status: str
    message: str
    jobs_found: int = 0
    jobs_analyzed: int = 0
    applications_created: int = 0
