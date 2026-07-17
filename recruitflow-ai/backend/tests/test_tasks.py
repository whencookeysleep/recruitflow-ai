from datetime import datetime, timedelta, timezone

from app.models import Candidate
from app.services.tasks import compute_tasks


def test_overdue_task_rules_are_deterministic(db) -> None:
    candidate = Candidate(
        name="钱二筛",
        current_stage="待用人部门二筛",
        current_status="active",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=30),
    )
    db.add(candidate)
    db.commit()

    tasks = compute_tasks(db)

    assert len(tasks) == 1
    assert tasks[0].candidate_id == candidate.id
    assert tasks[0].overdue_hours >= 5
