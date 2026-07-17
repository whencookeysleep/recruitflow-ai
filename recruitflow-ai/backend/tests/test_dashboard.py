from datetime import datetime, timedelta, timezone

from app.models import Candidate
from app.services.dashboard import dashboard_metrics


def test_dashboard_metrics_handles_sqlite_naive_datetimes(db) -> None:
    db.add(
        Candidate(
            name="周指标",
            applied_position="AI 产品经理",
            current_stage="待用人部门二筛",
            current_status="active",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )
    db.commit()

    metrics = dashboard_metrics(db)

    assert metrics.total_candidates == 1
    assert metrics.new_this_week == 1
