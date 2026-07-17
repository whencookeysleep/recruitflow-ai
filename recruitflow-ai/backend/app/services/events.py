from sqlalchemy.orm import Session

from app.models import RecruitmentEvent


def log_event(
    db: Session,
    event_type: str,
    *,
    candidate_id: int | None = None,
    actor: str = "system",
    old_stage: str | None = None,
    new_stage: str | None = None,
    note: str | None = None,
) -> RecruitmentEvent:
    event = RecruitmentEvent(
        event_type=event_type,
        candidate_id=candidate_id,
        actor=actor,
        old_stage=old_stage,
        new_stage=new_stage,
        note=note,
    )
    db.add(event)
    return event
