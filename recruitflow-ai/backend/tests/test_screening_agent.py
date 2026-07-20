from sqlalchemy import select

from app.config import Settings
from app.models import Candidate, JobDescription, RecruitmentEvent, ResumeFile, ScreeningAssessment
from app.schemas import AgentScreeningResult, JobDescriptionSpec, ScreeningDecisionRequest
from app.services import screening, screening_agent
from app.services.screening import confirm_agent_recommendation
from app.services.screening_agent import ModelUsage, run_screening_agent


def jd_spec() -> JobDescriptionSpec:
    return JobDescriptionSpec.model_validate(
        {
            "title": "后端开发工程师",
            "department": "AI 平台部",
            "must_have": [
                {"id": "python", "description": "掌握 Python", "weight": 60},
            ],
            "nice_to_have": [
                {"id": "fastapi", "description": "熟悉 FastAPI", "weight": 20},
            ],
            "screening_policy": {"pass_score": 70, "hold_score": 50},
        }
    )


def test_screening_agent_persists_grounded_assessment(db, monkeypatch) -> None:
    candidate = Candidate(
        name="李测试",
        applied_position="后端开发工程师",
        current_stage="待用人部门二筛",
        current_status="active",
    )
    db.add(candidate)
    db.flush()
    db.add(
        ResumeFile(
            filename="resume.pdf",
            file_path="resume.pdf",
            sha256="screening-sha",
            extracted_text="专业技能：Python、FastAPI。项目使用 FastAPI 开发接口。",
            parse_status="confirmed",
            candidate_id=candidate.id,
        )
    )
    spec = jd_spec()
    job = JobDescription(
        job_code="BE-001",
        title=spec.title,
        department=spec.department,
        version=1,
        status="active",
        content=spec.model_dump(mode="json"),
        created_by="Department Demo",
    )
    db.add(job)
    db.commit()

    result = AgentScreeningResult.model_validate(
        {
            "recommendation": "pass",
            "criteria_results": [
                {
                    "criterion_id": "python",
                    "matched": True,
                    "score": 60,
                    "evidence": ["专业技能：Python、FastAPI。"],
                    "reasoning": "简历明确列出 Python。",
                },
                {
                    "criterion_id": "fastapi",
                    "matched": True,
                    "score": 20,
                    "evidence": ["项目使用 FastAPI 开发接口。"],
                    "reasoning": "存在项目证据。",
                },
            ],
            "summary": "核心要求匹配。",
        }
    )
    monkeypatch.setattr(
        screening_agent,
        "_request_model",
        lambda resume_text, spec, settings, correction=None: (
            result,
            ModelUsage(input_tokens=100, output_tokens=50, api_cost=0.001),
        ),
    )

    assessment = run_screening_agent(db, candidate, job, Settings(ai_provider="openai"))

    assert assessment.total_score == 80
    assert assessment.recommendation == "pass"
    assert assessment.status == "agent_recommended"
    assert assessment.input_tokens == 100
    event = db.scalar(select(RecruitmentEvent).where(RecruitmentEvent.event_type == "agent_screening_completed"))
    assert event is not None


def test_grounding_rejects_non_resume_quote() -> None:
    result = AgentScreeningResult.model_validate(
        {
            "recommendation": "pass",
            "criteria_results": [
                {
                    "criterion_id": "python",
                    "matched": True,
                    "score": 60,
                    "evidence": ["不存在的证据"],
                    "reasoning": "invalid",
                },
                {
                    "criterion_id": "fastapi",
                    "matched": False,
                    "score": 0,
                    "evidence": [],
                    "reasoning": "not found",
                },
            ],
            "summary": "invalid",
        }
    )

    try:
        screening_agent._validate_grounding(result, "专业技能：Python", jd_spec())
    except ValueError as exc:
        assert "exact resume quote" in str(exc)
    else:
        raise AssertionError("Non-resume evidence must be rejected")


def experience_jd_spec() -> JobDescriptionSpec:
    payload = jd_spec().model_dump(mode="json")
    payload["experience"] = {"minimum_years": 2, "relevant_domains": ["后端开发"]}
    return JobDescriptionSpec.model_validate(payload)


def test_grounding_rejects_experience_inference_from_graduation_date() -> None:
    result = AgentScreeningResult.model_validate(
        {
            "recommendation": "reject",
            "criteria_results": [
                {"criterion_id": "python", "matched": True, "score": 60, "evidence": ["Python"], "reasoning": "matched"},
                {"criterion_id": "fastapi", "matched": False, "score": 0, "evidence": [], "reasoning": "not found"},
            ],
            "hard_requirement_failures": ["毕业时间：2025-06"],
            "summary": "根据毕业时间推断经验不足",
        }
    )

    try:
        screening_agent._validate_grounding(
            result,
            "专业技能：Python\n毕业时间：2025-06",
            experience_jd_spec(),
        )
    except ValueError as exc:
        assert "dates alone" in str(exc)
    else:
        raise AssertionError("Graduation date must not establish work experience")


def test_grounding_accepts_explicit_experience_contradiction() -> None:
    result = AgentScreeningResult.model_validate(
        {
            "recommendation": "reject",
            "criteria_results": [
                {"criterion_id": "python", "matched": True, "score": 60, "evidence": ["Python"], "reasoning": "matched"},
                {"criterion_id": "fastapi", "matched": False, "score": 0, "evidence": [], "reasoning": "not found"},
            ],
            "hard_requirement_failures": ["仅有 1 年后端开发经验"],
            "summary": "明确不满足两年经验要求",
        }
    )

    score = screening_agent._validate_grounding(
        result,
        "专业技能：Python\n仅有 1 年后端开发经验",
        experience_jd_spec(),
    )
    assert score == 60


def test_human_confirmation_changes_stage_and_syncs(db, monkeypatch) -> None:
    candidate = Candidate(
        name="确认候选人",
        current_stage="待用人部门二筛",
        current_status="active",
    )
    job = JobDescription(
        job_code="BE-002",
        title="后端开发工程师",
        department="AI 平台部",
        version=1,
        status="active",
        content=jd_spec().model_dump(mode="json"),
        created_by="Department Demo",
    )
    db.add_all([candidate, job])
    db.flush()
    assessment = ScreeningAssessment(
        candidate_id=candidate.id,
        job_description_id=job.id,
        recommendation="pass",
        total_score=80,
        criteria_results=[
            {
                "criterion_id": "python",
                "matched": True,
                "score": 60,
                "evidence": ["Python"],
                "reasoning": "matched",
            }
        ],
        summary="建议通过",
        model="deepseek/deepseek-v4-flash",
        prompt_version="screening-v1",
    )
    db.add(assessment)
    db.commit()

    class FakeSync:
        def sync_candidates(self, session, settings, candidate_ids=None):
            return object()

    monkeypatch.setattr(screening, "TencentDocsSyncAdapter", FakeSync)

    result = confirm_agent_recommendation(
        db,
        assessment,
        ScreeningDecisionRequest(decision="pass"),
        Settings(tencent_docs_token="test-token"),
        actor_name="李审批",
        actor_username="department_demo",
        actor_role="department",
    )

    assert result.status == "confirmed"
    assert result.sync_status == "synced"
    assert result.human_actor == "李审批"
    assert result.human_username == "department_demo"
    assert result.human_role == "department"
    assert candidate.current_stage == "待约面试"
