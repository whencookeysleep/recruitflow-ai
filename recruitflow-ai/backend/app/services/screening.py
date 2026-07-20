from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Candidate, JobDescription, ScreeningAssessment
from app.schemas import ScreeningDecisionRequest
from app.services.candidates import apply_screening_result
from app.services.events import log_event
from app.services.export import TencentDocsSyncAdapter
from app.services.screening_agent import run_screening_agent


def get_assessment_or_raise(db: Session, assessment_id: int) -> ScreeningAssessment:
    assessment = db.get(ScreeningAssessment, assessment_id)
    if assessment is None:
        raise ValueError(f"Screening assessment not found: {assessment_id}")
    return assessment


def list_candidate_assessments(db: Session, candidate_id: int) -> list[ScreeningAssessment]:
    return list(
        db.scalars(
            select(ScreeningAssessment)
            .where(ScreeningAssessment.candidate_id == candidate_id)
            .order_by(ScreeningAssessment.created_at.desc())
        ).all()
    )


def list_screening_assessments(
    db: Session,
    *,
    job_description_id: int | None = None,
    status: str | None = None,
) -> list[ScreeningAssessment]:
    query = select(ScreeningAssessment)
    if job_description_id is not None:
        query = query.where(ScreeningAssessment.job_description_id == job_description_id)
    if status is not None:
        query = query.where(ScreeningAssessment.status == status)
    return list(db.scalars(query.order_by(ScreeningAssessment.created_at.desc())).all())


def batch_screen_candidates(
    db: Session,
    job: JobDescription,
    settings: Settings,
    candidate_ids: list[int] | None,
) -> list[ScreeningAssessment]:
    query = select(Candidate).where(Candidate.current_status == "active")
    if candidate_ids is not None:
        if not candidate_ids:
            raise ValueError("candidate_ids must not be empty when provided")
        query = query.where(Candidate.id.in_(candidate_ids))
    else:
        query = query.where(
            Candidate.current_stage == "待用人部门二筛",
            Candidate.applied_position == job.title,
        )
    candidates = list(db.scalars(query.order_by(Candidate.id)).all())
    if not candidates:
        raise ValueError("No eligible candidates found for this JD")
    if candidate_ids is not None and len(candidates) != len(set(candidate_ids)):
        found = {candidate.id for candidate in candidates}
        missing = sorted(set(candidate_ids) - found)
        raise ValueError(f"Candidates not found or inactive: {missing}")
    return [run_screening_agent(db, candidate, job, settings) for candidate in candidates]


def confirm_agent_recommendation(
    db: Session,
    assessment: ScreeningAssessment,
    payload: ScreeningDecisionRequest,
    settings: Settings,
    *,
    actor_name: str,
    actor_username: str,
    actor_role: str,
) -> ScreeningAssessment:
    if assessment.status == "confirmed":
        raise ValueError("Screening assessment has already been confirmed")
    candidate = db.get(Candidate, assessment.candidate_id)
    if candidate is None:
        raise ValueError(f"Candidate not found: {assessment.candidate_id}")

    assessment.status = "confirmed"
    assessment.human_decision = payload.decision
    assessment.human_actor = actor_name
    assessment.human_username = actor_username
    assessment.human_role = actor_role
    assessment.human_note = payload.note
    assessment.confirmed_at = datetime.now(timezone.utc)
    candidate.matching_points = [
        evidence
        for item in assessment.criteria_results
        if item.get("matched")
        for evidence in item.get("evidence", [])
    ]
    candidate.risk_points = assessment.risk_points
    candidate.interview_questions = assessment.interview_questions
    candidate.ai_summary = assessment.summary
    apply_screening_result(
        db,
        candidate,
        payload.decision,
        actor=actor_name,
        note=f"assessment_id={assessment.id}; {payload.note or ''}".strip(),
    )

    try:
        TencentDocsSyncAdapter().sync_candidates(
            db,
            settings,
            candidate_ids=[candidate.id],
        )
    except Exception as exc:
        assessment.sync_status = "failed"
        log_event(
            db,
            "tencent_docs_sync_failed",
            candidate_id=candidate.id,
            actor="system",
            note=f"assessment_id={assessment.id}; error={exc}",
        )
        db.commit()
        raise RuntimeError(
            "Screening decision was saved, but Tencent Docs synchronization failed"
        ) from exc

    assessment.sync_status = "synced"
    log_event(
        db,
        "screening_decision_confirmed",
        candidate_id=candidate.id,
        actor=actor_name,
        note=(
            f"assessment_id={assessment.id}; agent={assessment.recommendation}; "
            f"human={payload.decision}; score={assessment.total_score}; "
            f"approver_name={actor_name}; approver_role={actor_role}; "
            f"approver_username={actor_username}"
        ),
    )
    db.commit()
    db.refresh(assessment)
    return assessment
