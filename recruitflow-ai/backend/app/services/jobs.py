from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import JobDescription
from app.schemas import JobDescriptionCreate, JobDescriptionUpdate


def create_job_description(db: Session, payload: JobDescriptionCreate) -> JobDescription:
    if payload.status == "active":
        for existing in db.scalars(
            select(JobDescription).where(
                JobDescription.job_code == payload.job_code,
                JobDescription.status == "active",
            )
        ):
            existing.status = "archived"
    job = JobDescription(
        job_code=payload.job_code,
        title=payload.jd.title,
        department=payload.jd.department,
        version=payload.version,
        status=payload.status,
        content=payload.jd.model_dump(mode="json"),
        created_by=payload.created_by,
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(f"JD {payload.job_code} version {payload.version} already exists") from exc
    db.refresh(job)
    return job


def list_job_descriptions(db: Session, *, status: str | None = None) -> list[JobDescription]:
    query = select(JobDescription)
    if status:
        query = query.where(JobDescription.status == status)
    return list(db.scalars(query.order_by(JobDescription.updated_at.desc())).all())


def get_job_description_or_raise(db: Session, job_description_id: int) -> JobDescription:
    job = db.get(JobDescription, job_description_id)
    if job is None:
        raise ValueError(f"Job description not found: {job_description_id}")
    return job


def update_job_description(
    db: Session, job: JobDescription, payload: JobDescriptionUpdate
) -> JobDescription:
    if payload.status is not None:
        job.status = payload.status
    if payload.jd is not None:
        job.title = payload.jd.title
        job.department = payload.jd.department
        job.content = payload.jd.model_dump(mode="json")
    if job.status == "active":
        for existing in db.scalars(
            select(JobDescription).where(
                JobDescription.job_code == job.job_code,
                JobDescription.id != job.id,
                JobDescription.status == "active",
            )
        ):
            existing.status = "archived"
    db.commit()
    db.refresh(job)
    return job
