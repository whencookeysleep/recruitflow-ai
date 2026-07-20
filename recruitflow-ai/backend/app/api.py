from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.auth import CurrentUser, authenticate, require_role
from app.models import Candidate, RecruitmentEvent, ResumeFile, ScreeningAssessment
from app.schemas import (
    BatchScreeningOut,
    BatchScreeningRequest,
    AiModelSettingsOut,
    AiModelSettingsUpdate,
    CandidateConfirmRequest,
    CandidateOut,
    CandidateUpdate,
    ChartPoint,
    CsvExportOut,
    DashboardTrendsOut,
    IntegrationSettingsOut,
    MetricsOut,
    JobDescriptionCreate,
    JobDescriptionOut,
    JobDescriptionUpdate,
    LoginOut,
    LoginRequest,
    NotificationOut,
    ParsedResume,
    RecruitmentEventOut,
    ResumeFileOut,
    ScreeningResultRequest,
    ScreeningAssessmentOut,
    ScreeningDecisionRequest,
    ScreeningRunRequest,
    StageUpdateRequest,
    TaskOut,
    TencentDocsSyncOut,
)
from app.services.candidates import apply_screening_result, get_candidate_or_raise, list_candidates, update_candidate, update_stage
from app.services.dashboard import dashboard_metrics, funnel, trends
from app.services.export import CSVSyncAdapter, TencentDocsSyncAdapter, integration_settings
from app.services.jobs import create_job_description, get_job_description_or_raise, list_job_descriptions, update_job_description
from app.services.files import MAX_PDF_BYTES, store_uploaded_pdf
from app.services.integrations import sync_candidate_integrations
from app.services.model_settings import get_ai_model_settings, update_ai_model_settings
from app.services.notifications import send_screening_card
from app.services.resumes import confirm_resume, ingest_pdf, parse_resume_record, parsed_to_confirm_request
from app.services.screening import batch_screen_candidates, confirm_agent_recommendation, get_assessment_or_raise, list_candidate_assessments, list_screening_assessments
from app.services.screening_agent import run_screening_agent
from app.services.tasks import compute_tasks

router = APIRouter(prefix="/api")


def bad_request(error: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(error))


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/login", response_model=LoginOut)
def login(payload: LoginRequest, settings: Settings = Depends(get_settings)) -> LoginOut:
    try:
        return authenticate(payload, settings)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/settings/ai-model", response_model=AiModelSettingsOut)
def ai_model_settings(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
) -> AiModelSettingsOut:
    return get_ai_model_settings(db, settings)


@router.patch("/settings/ai-model", response_model=AiModelSettingsOut)
def patch_ai_model_settings(
    payload: AiModelSettingsUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
) -> AiModelSettingsOut:
    return update_ai_model_settings(db, payload, settings)


@router.get("/settings/integrations", response_model=IntegrationSettingsOut)
def get_integration_settings(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> IntegrationSettingsOut:
    return integration_settings(db, settings)


@router.post("/resumes/upload", response_model=ResumeFileOut)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
) -> ResumeFile:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
    content = await file.read(MAX_PDF_BYTES + 1)
    try:
        target = store_uploaded_pdf(content, file.filename, settings.upload_dir)
        return ingest_pdf(db, target, settings, copy_file=False)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/resumes/{resume_id}/parse", response_model=ResumeFileOut)
def parse_resume_endpoint(
    resume_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
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
    background_tasks: BackgroundTasks,
    request: CandidateConfirmRequest | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
) -> Candidate:
    resume = db.get(ResumeFile, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if request is None:
        if not resume.parsed_payload:
            raise HTTPException(status_code=400, detail="Resume has no parsed payload")
        request = parsed_to_confirm_request(ParsedResume.model_validate(resume.parsed_payload))
    try:
        candidate = confirm_resume(db, resume, request)
        background_tasks.add_task(
            sync_candidate_integrations,
            candidate.id,
            settings,
            event_type="resume_confirmed",
            actor="HR",
        )
        return candidate
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/resumes/pending", response_model=list[ResumeFileOut])
def pending_resumes(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr")),
) -> list[ResumeFile]:
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
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> list[Candidate]:
    return list_candidates(db, search=search, position=position, stage=stage, owner=owner)


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def candidate_detail(
    candidate_id: int,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> Candidate:
    try:
        return get_candidate_or_raise(db, candidate_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
def patch_candidate(
    candidate_id: int,
    payload: CandidateUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
) -> Candidate:
    try:
        candidate = update_candidate(db, get_candidate_or_raise(db, candidate_id), payload)
        background_tasks.add_task(
            sync_candidate_integrations,
            candidate.id,
            settings,
            event_type="candidate_updated",
            actor="HR",
        )
        return candidate
    except Exception as exc:
        raise bad_request(exc) from exc


@router.patch("/candidates/{candidate_id}/stage", response_model=CandidateOut)
def patch_candidate_stage(
    candidate_id: int,
    payload: StageUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
) -> Candidate:
    try:
        payload.validate_stage()
        candidate = update_stage(db, get_candidate_or_raise(db, candidate_id), payload.stage, actor=payload.actor, note=payload.note)
        background_tasks.add_task(
            sync_candidate_integrations,
            candidate.id,
            settings,
            event_type="candidate_stage_changed",
            actor=payload.actor,
        )
        return candidate
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/candidates/{candidate_id}/events", response_model=list[RecruitmentEventOut])
def candidate_events(
    candidate_id: int,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> list[RecruitmentEvent]:
    return list(
        db.scalars(
            select(RecruitmentEvent)
            .where(RecruitmentEvent.candidate_id == candidate_id)
            .order_by(RecruitmentEvent.created_at.desc())
        ).all()
    )


@router.post("/candidates/{candidate_id}/screening-result", response_model=CandidateOut)
def screening_result(
    candidate_id: int,
    payload: ScreeningResultRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("department")),
) -> Candidate:
    try:
        candidate = apply_screening_result(db, get_candidate_or_raise(db, candidate_id), payload.result, actor=payload.actor, note=payload.note)
        background_tasks.add_task(
            sync_candidate_integrations,
            candidate.id,
            settings,
            event_type="screening_result",
            actor=payload.actor,
        )
        return candidate
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/candidates/{candidate_id}/send-screening-card", response_model=NotificationOut)
def send_card(
    candidate_id: int,
    assessment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> dict:
    try:
        assessment = get_assessment_or_raise(db, assessment_id) if assessment_id else None
        if assessment and assessment.candidate_id != candidate_id:
            raise ValueError("Assessment does not belong to this candidate")
        return send_screening_card(db, settings, get_candidate_or_raise(db, candidate_id), assessment)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/job-descriptions", response_model=JobDescriptionOut)
def create_jd(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("department")),
) -> JobDescriptionOut:
    payload.created_by = user.display_name
    try:
        return create_job_description(db, payload)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/job-descriptions", response_model=list[JobDescriptionOut])
def job_descriptions(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("hr", "department")),
) -> list:
    return list_job_descriptions(db, status=status)


@router.patch("/job-descriptions/{job_description_id}", response_model=JobDescriptionOut)
def patch_job_description(
    job_description_id: int,
    payload: JobDescriptionUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("department")),
) -> JobDescriptionOut:
    try:
        return update_job_description(db, get_job_description_or_raise(db, job_description_id), payload)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/candidates/{candidate_id}/agent-screen", response_model=ScreeningAssessmentOut)
def agent_screen_candidate(
    candidate_id: int,
    payload: ScreeningRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: CurrentUser = Depends(require_role("department")),
) -> ScreeningAssessment:
    try:
        assessment = run_screening_agent(
            db,
            get_candidate_or_raise(db, candidate_id),
            get_job_description_or_raise(db, payload.job_description_id),
            settings,
        )
        background_tasks.add_task(
            sync_candidate_integrations,
            candidate_id,
            settings,
            event_type="agent_screening_completed",
            actor=user.display_name,
            assessment_id=assessment.id,
        )
        return assessment
    except Exception as exc:
        raise bad_request(exc) from exc


@router.post("/job-descriptions/{job_description_id}/screen-pending", response_model=BatchScreeningOut)
def agent_screen_pending(
    job_description_id: int,
    payload: BatchScreeningRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: CurrentUser = Depends(require_role("department")),
) -> BatchScreeningOut:
    try:
        assessments = batch_screen_candidates(
            db,
            get_job_description_or_raise(db, job_description_id),
            settings,
            payload.candidate_ids,
        )
        for assessment in assessments:
            background_tasks.add_task(
                sync_candidate_integrations,
                assessment.candidate_id,
                settings,
                event_type="agent_screening_completed",
                actor=user.display_name,
                assessment_id=assessment.id,
            )
        return BatchScreeningOut(job_description_id=job_description_id, assessments=assessments)
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/candidates/{candidate_id}/assessments", response_model=list[ScreeningAssessmentOut])
def candidate_assessments(
    candidate_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("hr", "department")),
) -> list[ScreeningAssessment]:
    get_candidate_or_raise(db, candidate_id)
    return list_candidate_assessments(db, candidate_id)


@router.get("/screening-assessments", response_model=list[ScreeningAssessmentOut])
def screening_assessments(
    job_description_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> list[ScreeningAssessment]:
    return list_screening_assessments(
        db,
        job_description_id=job_description_id,
        status=status,
    )


@router.post("/screening-assessments/{assessment_id}/confirm", response_model=ScreeningAssessmentOut)
def confirm_screening_assessment(
    assessment_id: int,
    payload: ScreeningDecisionRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: CurrentUser = Depends(require_role("department")),
) -> ScreeningAssessment:
    try:
        return confirm_agent_recommendation(
            db,
            get_assessment_or_raise(db, assessment_id),
            payload,
            settings,
            actor_name=user.display_name,
            actor_username=user.username,
            actor_role=user.role,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise bad_request(exc) from exc


@router.get("/dashboard/metrics", response_model=MetricsOut)
def metrics(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> MetricsOut:
    return dashboard_metrics(db)


@router.get("/dashboard/funnel", response_model=list[ChartPoint])
def dashboard_funnel(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> list[ChartPoint]:
    return funnel(db)


@router.get("/dashboard/trends", response_model=DashboardTrendsOut)
def dashboard_trends(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> DashboardTrendsOut:
    return trends(db)


@router.get("/tasks", response_model=list[TaskOut])
def tasks(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> list[TaskOut]:
    return compute_tasks(db)


@router.get("/events", response_model=list[RecruitmentEventOut])
def events(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> list[RecruitmentEvent]:
    return list(db.scalars(select(RecruitmentEvent).order_by(RecruitmentEvent.created_at.desc()).limit(200)).all())


@router.post("/export/csv", response_model=CsvExportOut)
def export_csv(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr")),
) -> CsvExportOut:
    return CSVSyncAdapter().export_candidates(db, settings)


@router.post("/export/tencent-docs", response_model=TencentDocsSyncOut)
def sync_tencent_docs(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: CurrentUser = Depends(require_role("hr", "department")),
) -> TencentDocsSyncOut:
    try:
        return TencentDocsSyncAdapter().sync_candidates(db, settings)
    except Exception as exc:
        raise bad_request(exc) from exc
