from abc import ABC, abstractmethod

import httpx
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Candidate, NotificationLog
from app.services.events import log_event


class NotificationAdapter(ABC):
    @abstractmethod
    def send_screening_card(self, candidate: Candidate) -> dict:
        raise NotImplementedError


def build_screening_card(candidate: Candidate) -> dict:
    return {
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


class MockWeComAdapter(NotificationAdapter):
    def send_screening_card(self, candidate: Candidate) -> dict:
        return {"channel": "mock_wecom", "status": "sent", "payload": build_screening_card(candidate)}


class WeComWebhookAdapter(NotificationAdapter):
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send_screening_card(self, candidate: Candidate) -> dict:
        card = build_screening_card(candidate)
        markdown = f"### {card['title']}\n\n{card.get('summary') or '无摘要'}"
        response = httpx.post(self.webhook_url, json={"msgtype": "markdown", "markdown": {"content": markdown}}, timeout=15)
        response.raise_for_status()
        return {"channel": "wecom_webhook", "status": "sent", "payload": card, "response": response.text}


def adapter_from_settings(settings: Settings) -> NotificationAdapter:
    if settings.wecom_webhook_url:
        return WeComWebhookAdapter(settings.wecom_webhook_url)
    return MockWeComAdapter()


def send_screening_card(db: Session, settings: Settings, candidate: Candidate) -> dict:
    result = adapter_from_settings(settings).send_screening_card(candidate)
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
