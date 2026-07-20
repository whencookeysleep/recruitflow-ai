from app.config import Settings
from app.database import SessionLocal
from app.models import Candidate, ScreeningAssessment
from app.services.events import log_event
from app.services.export import TencentDocsSyncAdapter
from app.services.notifications import send_screening_card


def sync_candidate_integrations(
    candidate_id: int,
    settings: Settings,
    *,
    event_type: str,
    actor: str,
    assessment_id: int | None = None,
) -> None:
    """Run optional external integrations after the primary database response is ready."""
    db = SessionLocal()
    try:
        candidate = db.get(Candidate, candidate_id)
        if candidate is None:
            log_event(
                db,
                "integration_sync_failed",
                candidate_id=candidate_id,
                actor="system",
                note=f"trigger={event_type}; error=candidate not found",
            )
            db.commit()
            return

        assessment = db.get(ScreeningAssessment, assessment_id) if assessment_id else None
        _sync_tencent_docs(db, candidate, assessment, settings, event_type, actor)
        if assessment is not None:
            _send_wecom_notification(db, candidate, assessment, settings, event_type)
    finally:
        db.close()


def _sync_tencent_docs(
    db,
    candidate: Candidate,
    assessment: ScreeningAssessment | None,
    settings: Settings,
    event_type: str,
    actor: str,
) -> None:
    if not settings.tencent_docs_token:
        if assessment is not None:
            assessment.sync_status = "unconfigured"
        log_event(
            db,
            "tencent_docs_sync_skipped",
            candidate_id=candidate.id,
            actor="system",
            note=f"trigger={event_type}; reason=TENCENT_DOCS_TOKEN is not configured",
        )
        db.commit()
        return

    try:
        result = TencentDocsSyncAdapter().sync_candidates(
            db,
            settings,
            candidate_ids=[candidate.id],
        )
    except Exception as exc:
        db.rollback()
        if assessment is not None:
            assessment.sync_status = "failed"
        log_event(
            db,
            "tencent_docs_sync_failed",
            candidate_id=candidate.id,
            actor="system",
            note=f"trigger={event_type}; error={exc}",
        )
        db.commit()
        return

    if assessment is not None:
        assessment.sync_status = "synced"
    log_event(
        db,
        "tencent_docs_auto_synced",
        candidate_id=candidate.id,
        actor=actor,
        note=f"trigger={event_type}; rows={result.rows}; file_id={result.file_id}",
    )
    db.commit()


def _send_wecom_notification(
    db,
    candidate: Candidate,
    assessment: ScreeningAssessment,
    settings: Settings,
    event_type: str,
) -> None:
    if not settings.wecom_webhook_url:
        log_event(
            db,
            "wecom_notification_skipped",
            candidate_id=candidate.id,
            actor="system",
            note=f"trigger={event_type}; reason=WECOM_WEBHOOK_URL is not configured",
        )
        db.commit()
        return

    try:
        send_screening_card(db, settings, candidate, assessment)
    except Exception as exc:
        db.rollback()
        log_event(
            db,
            "wecom_notification_failed",
            candidate_id=candidate.id,
            actor="system",
            note=f"trigger={event_type}; assessment_id={assessment.id}; error={exc}",
        )
        db.commit()
