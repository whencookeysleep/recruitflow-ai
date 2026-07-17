import json
import re

import httpx

from app.config import Settings
from app.schemas import ParsedResume


def _match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _list_from_keywords(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword.lower() in text.lower()]


def mock_parse_resume(text: str) -> ParsedResume:
    name = _match(r"(?:姓名|Name)[:：]\s*([^\n]+)", text)
    phone = _match(r"(?:电话|手机|Phone)[:：]\s*([+0-9\- ]{7,})", text)
    email = _match(r"(?:邮箱|Email)[:：]\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", text)
    school = _match(r"(?:学校|University|School)[:：]\s*([^\n]+)", text)
    degree = _match(r"(?:学历|Degree)[:：]\s*([^\n]+)", text)
    major = _match(r"(?:专业|Major)[:：]\s*([^\n]+)", text)
    graduation_date = _match(r"(?:毕业时间|Graduation)[:：]\s*([^\n]+)", text)
    position = _match(r"(?:应聘岗位|Position)[:：]\s*([^\n]+)", text)
    skills = _list_from_keywords(
        text,
        ["Python", "FastAPI", "SQL", "测试", "自动化", "产品设计", "数据分析", "LLM", "React", "Java"],
    )
    projects = re.findall(r"(?:项目|Project)[:：]\s*([^\n]+)", text)
    work = re.findall(r"(?:工作经历|Work)[:：]\s*([^\n]+)", text)
    internships = re.findall(r"(?:实习经历|Internship)[:：]\s*([^\n]+)", text)
    matching_points = skills[:3] or ["简历包含岗位相关经历，需人工确认匹配度"]
    risk_points = [] if confidence_from_text(text) > 0.65 else ["简历结构化字段较少，建议人工补充确认"]
    summary_name = name or "候选人"
    summary = f"{summary_name} 应聘 {position or '待确认岗位'}，具备 {', '.join(skills[:4]) if skills else '若干相关'} 经验。"
    return ParsedResume(
        name=name,
        phone=phone,
        email=email,
        school=school,
        degree=degree,
        major=major,
        graduation_date=graduation_date,
        applied_position=position,
        skills=skills,
        internship_experience=internships,
        project_experience=projects,
        work_experience=work,
        summary=summary,
        matching_points=matching_points,
        risk_points=risk_points,
        interview_questions=[
            "请结合最近一个项目说明你的职责和结果。",
            "你如何判断当前岗位的核心成功指标？",
        ],
        confidence=confidence_from_text(text),
    )


def confidence_from_text(text: str) -> float:
    fields = ["姓名", "Name", "电话", "Phone", "邮箱", "Email", "学校", "专业", "应聘岗位", "Position"]
    hits = sum(1 for field in fields if field.lower() in text.lower())
    return min(0.95, max(0.35, hits / 8))


def parse_resume(text: str, settings: Settings) -> ParsedResume:
    if settings.ai_provider == "mock":
        return mock_parse_resume(text)
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER is not mock")

    schema = ParsedResume.model_json_schema()
    prompt = (
        "Extract only facts traceable to the resume text. Do not infer gender or age. "
        "Return JSON matching this schema exactly.\n"
        f"Schema: {json.dumps(schema, ensure_ascii=False)}\n"
        f"Resume:\n{text}"
    )
    response = httpx.post(
        f"{settings.openai_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": "You parse resumes into strict JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=45,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return ParsedResume.model_validate_json(content)
