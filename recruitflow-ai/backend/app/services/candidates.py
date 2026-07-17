from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate, STAGES
from app.schemas import CandidateUpdate
from app.services.events import log_event


def get_candidate_or_raise(db: Session, candidate_id: int) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    return candidate


def list_candidates(
    db: Session,
    *,
    search: str | None = None,
    position: str | None = None,
    stage: str | None = None,
    owner: str | None = None,
) -> list[Candidate]:
    query = select(Candidate).where(Candidate.current_status != "pending_confirmation")
    if search:
        pattern = f"%{search}%"
        query = query.where(Candidate.name.like(pattern) | Candidate.school.like(pattern) | Candidate.email.like(pattern))
    if position:
        query = query.where(Candidate.applied_position == position)
    if stage:
        query = query.where(Candidate.current_stage == stage)
    if owner:
        query = query.where(Candidate.hr_owner == owner)
    return list(db.scalars(query.order_by(Candidate.updated_at.desc())).all())


def update_candidate(db: Session, candidate: Candidate, payload: CandidateUpdate) -> Candidate:
    for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(candidate, field, value)
    log_event(db, "candidate_updated", candidate_id=candidate.id, actor="HR", new_stage=candidate.current_stage)
    db.commit()
    db.refresh(candidate)
    return candidate


def update_stage(db: Session, candidate: Candidate, stage: str, *, actor: str, note: str | None = None) -> Candidate:
    if stage not in STAGES:
        raise ValueError(f"Unsupported recruitment stage: {stage}")
    old_stage = candidate.current_stage
    candidate.current_stage = stage
    log_event(
        db,
        "candidate_stage_changed",
        candidate_id=candidate.id,
        actor=actor,
        old_stage=old_stage,
        new_stage=stage,
        note=note,
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def apply_screening_result(
    db: Session,
    candidate: Candidate,
    result: str,
    *,
    actor: str,
    note: str | None = None,
) -> Candidate:
    if result == "pass":
        next_stage = "待约面试"
    elif result == "reject":
        next_stage = "二筛不通过"
    elif result == "hold":
        next_stage = "待用人部门二筛"
    else:
        raise ValueError(f"Unsupported screening result: {result}")
    log_event(db, "screening_result", candidate_id=candidate.id, actor=actor, old_stage=candidate.current_stage, new_stage=next_stage, note=note)
    candidate.current_stage = next_stage
    db.commit()
    db.refresh(candidate)
    return candidate
