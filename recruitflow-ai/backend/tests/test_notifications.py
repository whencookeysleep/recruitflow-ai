from app.config import Settings
from app.models import Candidate, JobDescription, ScreeningAssessment
from app.services.notifications import MockWeComAdapter, send_screening_card


def test_screening_notification_contains_assessment_and_candidate_id(db) -> None:
    candidate = Candidate(name="通知候选人", applied_position="后端开发工程师", current_status="active")
    job = JobDescription(
        job_code="BE-003",
        title="后端开发工程师",
        department="AI 平台部",
        version=1,
        status="active",
        content={},
        created_by="Department Demo",
    )
    db.add_all([candidate, job])
    db.flush()
    assessment = ScreeningAssessment(
        candidate_id=candidate.id,
        job_description_id=job.id,
        recommendation="pass",
        total_score=88,
        criteria_results=[],
        summary="建议通过",
        model="deepseek/deepseek-v4-flash",
        prompt_version="screening-v1",
    )
    db.add(assessment)
    db.commit()

    result = send_screening_card(
        db,
        Settings(public_app_url="https://demo.example.com"),
        candidate,
        assessment,
        adapter=MockWeComAdapter(),
    )

    assert result["candidate_id"] == candidate.id
    assert result["payload"]["score"] == 88
    assert result["payload"]["confirmation_url"].endswith(
        f"/candidates/{candidate.id}?assessment={assessment.id}"
    )
