from abc import ABC, abstractmethod

import httpx
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Candidate, JobDescription, NotificationLog, ScreeningAssessment
from app.services.events import log_event


class NotificationAdapter(ABC):
    @abstractmethod
    def send_screening_card(self, candidate: Candidate, card: dict) -> dict:
        raise NotImplementedError


def build_screening_card(
    candidate: Candidate,
    *,
    assessment: ScreeningAssessment | None = None,
    job: JobDescription | None = None,
    public_app_url: str | None = None,
) -> dict:
    card = {
        "title": f"{candidate.name or '候选人'} - {candidate.applied_position or '岗位待确认'}",
        "school": candidate.school,
        "major": candidate.major,
        "degree": candidate.degree,
        "summary": candidate.ai_summary,
        "matching_points": candidate.matching_points,
        "risk_points": candidate.risk_points,
        "actions": ["通过", "不通过", "待沟通"],
        "resume_link": candidate.resume_file_path,
        "ai_generated": True,
    }
    if assessment is not None:
        card.update(
            {
                "assessment_id": assessment.id,
                "job_code": job.job_code if job else None,
                "score": assessment.total_score,
                "recommendation": assessment.recommendation,
                "criteria_results": assessment.criteria_results,
                "confirmation_url": (
                    f"{public_app_url.rstrip('/')}/candidates/{candidate.id}?assessment={assessment.id}"
                    if public_app_url
                    else None
                ),
            }
        )
    return card


class MockWeComAdapter(NotificationAdapter):
    def send_screening_card(self, candidate: Candidate, card: dict) -> dict:
        return {"channel": "mock_wecom", "status": "sent", "payload": card}


class WeComWebhookAdapter(NotificationAdapter):
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send_screening_card(self, candidate: Candidate, card: dict) -> dict:
        markdown = f"### {card['title']}\n\n{card.get('summary') or '无摘要'}"
        if card.get("assessment_id"):
            markdown += (
                f"\n\n**AI 二筛：{card['score']} 分 / {card['recommendation']}**"
                f"\n\n[进入系统确认结果]({card['confirmation_url']})"
            )
        response = httpx.post(self.webhook_url, json={"msgtype": "markdown", "markdown": {"content": markdown}}, timeout=15)
        response.raise_for_status()
        return {"channel": "wecom_webhook", "status": "sent", "payload": card, "response": response.text}


def adapter_from_settings(settings: Settings) -> NotificationAdapter:
    if settings.wecom_webhook_url:
        return WeComWebhookAdapter(settings.wecom_webhook_url)
    raise ValueError("WECOM_WEBHOOK_URL is required for a real WeCom group notification")


def send_screening_card(
    db: Session,
    settings: Settings,
    candidate: Candidate,
    assessment: ScreeningAssessment | None = None,
    adapter: NotificationAdapter | None = None,
) -> dict:
    job = db.get(JobDescription, assessment.job_description_id) if assessment else None
    card = build_screening_card(
        candidate,
        assessment=assessment,
        job=job,
        public_app_url=settings.public_app_url,
    )
    result = (adapter or adapter_from_settings(settings)).send_screening_card(candidate, card)
    result["candidate_id"] = candidate.id
    db.add(
        NotificationLog(
            candidate_id=candidate.id,
            channel=result["channel"],
            status=result["status"],
            payload=result["payload"],
            response=result.get("response"),
        )
    )
    log_event(db, "notification_sent", candidate_id=candidate.id, actor="HR", note=f"channel={result['channel']}")
    db.commit()
    return result
