from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Candidate, RecruitmentEvent, ResumeFile
from app.schemas import (
    CandidateConfirmRequest,
    CandidateOut,
    CandidateUpdate,
    ChartPoint,
    CsvExportOut,
    DashboardTrendsOut,
    MetricsOut,
    NotificationOut,
    ParsedResume,
    RecruitmentEventOut,
    ResumeFileOut,
    ScreeningResultRequest,
    StageUpdateRequest,
    TaskOut,
)
from app.services.candidates import apply_screening_result, get_candidate_or_raise, list_candidates, update_candidate, update_stage
from app.services.dashboard import dashboard_metrics, funnel, trends
from app.services.export import MockTencentDocAdapter
from app.services.notifications import send_screening_card
from app.services.resumes import confirm_resume, ingest_pdf, parse_resume_record, parsed_to_confirm_request
from app.services.tasks import compute_tasks

router = APIRouter(prefix="/api")


def bad_request(error: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(error))


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/resumes/upload", response_model=ResumeFileOut)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ResumeFile:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    target = settings.upload_dir / Path(file.filename).name
    content = await file.read()
    target.write_bytes(content)
    try:
        return ingest_pdf(db, target, settings, copy_file=False)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/resumes/{resume_id}/parse", response_model=ResumeFileOut)
def parse_resume_endpoint(
    resume_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ResumeFile:
    resume = db.get(ResumeFile, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    try:
        result = parse_resume_record(db, resume, settings)
        db.commit()
        db.refresh(result)
        return result
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/resumes/{resume_id}/confirm", response_model=CandidateOut)
def confirm_resume_endpoint(
    resume_id: int,
    request: CandidateConfirmRequest | None = None,
    db: Session = Depends(get_db),
) -> Candidate:
    resume = db.get(ResumeFile, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if request is None:
        if not resume.parsed_payload:
            raise HTTPException(status_code=400, detail="Resume has no parsed payload")
        request = parsed_to_confirm_request(ParsedResume.model_validate(resume.parsed_payload))
    try:
        return confirm_resume(db, resume, request)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/resumes/pending", response_model=list[ResumeFileOut])
def pending_resumes(db: Session = Depends(get_db)) -> list[ResumeFile]:
    return list(
        db.scalars(
            select(ResumeFile).where(ResumeFile.parse_status.in_(["pending_confirmation", "possible_duplicate"]))
        ).all()
    )


@router.get("/candidates", response_model=list[CandidateOut])
def candidates(
    search: str | None = None,
    position: str | None = None,
    stage: str | None = None,
    owner: str | None = None,
    db: Session = Depends(get_db),
) -> list[Candidate]:
    return list_candidates(db, search=search, position=position, stage=stage, owner=owner)


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def candidate_detail(candidate_id: int, db: Session = Depends(get_db)) -> Candidate:
    try:
        return get_candidate_or_raise(db, candidate_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
def patch_candidate(candidate_id: int, payload: CandidateUpdate, db: Session = Depends(get_db)) -> Candidate:
    try:
        return update_candidate(db, get_candidate_or_raise(db, candidate_id), payload)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.patch("/candidates/{candidate_id}/stage", response_model=CandidateOut)
def patch_candidate_stage(candidate_id: int, payload: StageUpdateRequest, db: Session = Depends(get_db)) -> Candidate:
    try:
        payload.validate_stage()
        return update_stage(db, get_candidate_or_raise(db, candidate_id), payload.stage, actor=payload.actor, note=payload.note)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/candidates/{candidate_id}/events", response_model=list[RecruitmentEventOut])
def candidate_events(candidate_id: int, db: Session = Depends(get_db)) -> list[RecruitmentEvent]:
    return list(
        db.scalars(
            select(RecruitmentEvent)
            .where(RecruitmentEvent.candidate_id == candidate_id)
            .order_by(RecruitmentEvent.created_at.desc())
        ).all()
    )


@router.post("/candidates/{candidate_id}/screening-result", response_model=CandidateOut)
def screening_result(candidate_id: int, payload: ScreeningResultRequest, db: Session = Depends(get_db)) -> Candidate:
    try:
        return apply_screening_result(db, get_candidate_or_raise(db, candidate_id), payload.result, actor=payload.actor, note=payload.note)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/candidates/{candidate_id}/send-screening-card", response_model=NotificationOut)
def send_card(
    candidate_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    try:
        return send_screening_card(db, settings, get_candidate_or_raise(db, candidate_id))
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/dashboard/metrics", response_model=MetricsOut)
def metrics(db: Session = Depends(get_db)) -> MetricsOut:
    return dashboard_metrics(db)


@router.get("/dashboard/funnel", response_model=list[ChartPoint])
def dashboard_funnel(db: Session = Depends(get_db)) -> list[ChartPoint]:
    return funnel(db)


@router.get("/dashboard/trends", response_model=DashboardTrendsOut)
def dashboard_trends(db: Session = Depends(get_db)) -> DashboardTrendsOut:
    return trends(db)


@router.get("/tasks", response_model=list[TaskOut])
def tasks(db: Session = Depends(get_db)) -> list[TaskOut]:
    return compute_tasks(db)


@router.get("/events", response_model=list[RecruitmentEventOut])
def events(db: Session = Depends(get_db)) -> list[RecruitmentEvent]:
    return list(db.scalars(select(RecruitmentEvent).order_by(RecruitmentEvent.created_at.desc()).limit(200)).all())


@router.post("/export/csv", response_model=CsvExportOut)
def export_csv(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> CsvExportOut:
    return MockTencentDocAdapter().export_candidates(db, settings)
