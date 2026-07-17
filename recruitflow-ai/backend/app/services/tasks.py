from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate
from app.schemas import TaskOut


TIMEOUT_RULES = {
    "待用人部门二筛": 24,
    "二筛通过": 24,
    "面试完成": 24,
    "Offer 待审批": 48,
    "Offer 已发放": 48,
}


def overdue_hours(candidate: Candidate, now: datetime) -> float:
    limit = TIMEOUT_RULES.get(candidate.current_stage)
    if not limit:
        return 0.0
    updated_at = candidate.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    delta = now - updated_at
    hours = delta.total_seconds() / 3600
    return max(0.0, hours - limit)


def compute_tasks(db: Session) -> list[TaskOut]:
    now = datetime.now(timezone.utc)
    candidates = db.scalars(select(Candidate).where(Candidate.current_status == "active")).all()
    tasks: list[TaskOut] = []
    for candidate in candidates:
        hours = overdue_hours(candidate, now)
        candidate.is_overdue = hours > 0
        if hours > 0:
            tasks.append(
                TaskOut(
                    candidate_id=candidate.id,
                    candidate_name=candidate.name,
                    stage=candidate.current_stage,
                    department=candidate.department,
                    overdue_hours=round(hours, 1),
                    reminder_text=f"请跟进 {candidate.name or '候选人'} 的 {candidate.current_stage}，已超时 {round(hours, 1)} 小时。",
                )
            )
    db.commit()
    return tasks
