from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate, STAGES
from app.schemas import ChartPoint, DashboardTrendsOut, MetricsOut
from app.services.tasks import compute_tasks


def dashboard_metrics(db: Session) -> MetricsOut:
    candidates = list(db.scalars(select(Candidate).where(Candidate.current_status == "active")).all())
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    overdue_count = len(compute_tasks(db))
    return MetricsOut(
        total_candidates=len(candidates),
        new_this_week=sum(1 for candidate in candidates if candidate.created_at >= week_start),
        pending_screening=sum(1 for candidate in candidates if candidate.current_stage == "待用人部门二筛"),
        pending_interview_schedule=sum(1 for candidate in candidates if candidate.current_stage in {"二筛通过", "待约面试"}),
        pending_feedback=sum(1 for candidate in candidates if candidate.current_stage == "待面试反馈"),
        overdue=overdue_count,
        offers=sum(1 for candidate in candidates if candidate.current_stage in {"Offer 待审批", "Offer 已发放"}),
    )


def funnel(db: Session) -> list[ChartPoint]:
    candidates = list(db.scalars(select(Candidate).where(Candidate.current_status == "active")).all())
    counts = Counter(candidate.current_stage for candidate in candidates)
    return [ChartPoint(name=stage, value=counts.get(stage, 0)) for stage in STAGES if counts.get(stage, 0)]


def trends(db: Session) -> DashboardTrendsOut:
    candidates = list(db.scalars(select(Candidate).where(Candidate.current_status == "active")).all())
    today = datetime.now(timezone.utc).date()
    recent = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        recent.append(ChartPoint(name=day.isoformat(), value=sum(1 for c in candidates if c.created_at.date() == day)))
    position_counts = Counter(candidate.applied_position or "未填写" for candidate in candidates)
    stage_counts = Counter(candidate.current_stage for candidate in candidates)
    stage_hours: dict[str, list[float]] = defaultdict(list)
    now = datetime.now(timezone.utc)
    for candidate in candidates:
        updated_at = candidate.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        stage_hours[candidate.current_stage].append((now - updated_at).total_seconds() / 3600)
    return DashboardTrendsOut(
        recent_seven_days=recent,
        position_counts=[ChartPoint(name=name, value=value) for name, value in position_counts.items()],
        stage_distribution=[ChartPoint(name=name, value=value) for name, value in stage_counts.items()],
        average_stage_hours=[
            ChartPoint(name=name, value=round(sum(values) / len(values), 1)) for name, values in stage_hours.items()
        ],
    )
