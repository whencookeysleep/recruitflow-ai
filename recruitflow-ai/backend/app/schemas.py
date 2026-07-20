from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models import STAGES


class ParsedResume(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    school: str | None = None
    degree: str | None = None
    major: str | None = None
    graduation_date: str | None = None
    applied_position: str | None = None
    skills: list[str] = Field(default_factory=list)
    internship_experience: list[str] = Field(default_factory=list)
    project_experience: list[str] = Field(default_factory=list)
    work_experience: list[str] = Field(default_factory=list)
    summary: str | None = None
    matching_points: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ResumeFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    sha256: str
    parse_status: str
    extracted_text: str
    parsed_payload: dict | None
    duplicate_candidate_id: int | None
    candidate_id: int | None
    created_at: datetime


class CandidateBase(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    school: str | None = None
    major: str | None = None
    degree: str | None = None
    graduation_date: str | None = None
    applied_position: str | None = None
    department: str | None = None
    hr_owner: str | None = None
    interviewer: str | None = None
    interview_time: datetime | None = None
    ai_summary: str | None = None


class CandidateUpdate(CandidateBase):
    current_status: str | None = None


class CandidateConfirmRequest(CandidateBase):
    skills: list[str] = Field(default_factory=list)
    matching_points: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    create_new_if_duplicate: bool = False


class CandidateOut(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_source: str
    current_stage: str
    current_status: str
    is_overdue: bool
    resume_file_path: str | None
    skills: list[str]
    matching_points: list[str]
    risk_points: list[str]
    interview_questions: list[str]
    confidence: float
    created_at: datetime
    updated_at: datetime


class StageUpdateRequest(BaseModel):
    stage: str
    actor: str = "HR"
    note: str | None = None

    def validate_stage(self) -> None:
        if self.stage not in STAGES:
            raise ValueError(f"Unsupported recruitment stage: {self.stage}")


class ScreeningResultRequest(BaseModel):
    result: str = Field(pattern="^(pass|reject|hold)$")
    actor: str = "HR"
    note: str | None = None


class JobCriterion(BaseModel):
    id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    description: str = Field(min_length=2, max_length=500)
    weight: int = Field(ge=1, le=100)


class EducationRequirement(BaseModel):
    minimum_degree: str | None = None
    preferred_majors: list[str] = Field(default_factory=list)


class ExperienceRequirement(BaseModel):
    minimum_years: float | None = Field(default=None, ge=0, le=50)
    relevant_domains: list[str] = Field(default_factory=list)


class ScreeningPolicy(BaseModel):
    pass_score: float = Field(default=75, ge=0, le=100)
    hold_score: float = Field(default=55, ge=0, le=100)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "ScreeningPolicy":
        if self.pass_score <= self.hold_score:
            raise ValueError("pass_score must be greater than hold_score")
        return self


class JobDescriptionSpec(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    department: str = Field(min_length=2, max_length=120)
    summary: str = Field(default="", max_length=1000)
    responsibilities: list[str] = Field(default_factory=list)
    location: str = Field(default="上海 / 可远程协作", max_length=120)
    employment_type: str = Field(default="全职", max_length=80)
    must_have: list[JobCriterion] = Field(min_length=1)
    nice_to_have: list[JobCriterion] = Field(default_factory=list)
    education: EducationRequirement | None = None
    experience: ExperienceRequirement | None = None
    disqualifiers: list[str] = Field(default_factory=list)
    screening_policy: ScreeningPolicy = Field(default_factory=ScreeningPolicy)

    @model_validator(mode="after")
    def validate_criteria(self) -> "JobDescriptionSpec":
        criteria = self.must_have + self.nice_to_have
        ids = [criterion.id for criterion in criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("criterion ids must be unique")
        total_weight = sum(criterion.weight for criterion in criteria)
        if total_weight > 100:
            raise ValueError("criterion weights must total no more than 100")
        if self.screening_policy.pass_score > total_weight:
            raise ValueError("pass_score cannot exceed the total criterion weight")
        if self.screening_policy.hold_score > total_weight:
            raise ValueError("hold_score cannot exceed the total criterion weight")
        return self


class JobDescriptionCreate(BaseModel):
    job_code: str = Field(min_length=2, max_length=80)
    version: int = Field(default=1, ge=1)
    status: Literal["draft", "active", "archived"] = "draft"
    created_by: str = Field(default="Department Demo", min_length=1, max_length=120)
    jd: JobDescriptionSpec


class JobDescriptionUpdate(BaseModel):
    status: Literal["draft", "active", "archived"] | None = None
    jd: JobDescriptionSpec | None = None


class JobDescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_code: str
    title: str
    department: str
    version: int
    status: str
    content: dict
    created_by: str
    created_at: datetime
    updated_at: datetime


class CriterionAssessment(BaseModel):
    criterion_id: str
    matched: bool
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    reasoning: str


class AgentScreeningResult(BaseModel):
    recommendation: Literal["pass", "hold", "reject"]
    criteria_results: list[CriterionAssessment]
    hard_requirement_failures: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    summary: str


class ScreeningRunRequest(BaseModel):
    job_description_id: int


class BatchScreeningRequest(BaseModel):
    candidate_ids: list[int] | None = None


class ScreeningDecisionRequest(BaseModel):
    decision: Literal["pass", "reject", "hold"]
    note: str | None = None


class ScreeningAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_description_id: int
    recommendation: str
    total_score: float
    criteria_results: list[dict]
    hard_requirement_failures: list[str]
    risk_points: list[str]
    interview_questions: list[str]
    summary: str
    model: str
    prompt_version: str
    status: str
    human_decision: str | None
    human_actor: str | None
    human_username: str | None
    human_role: str | None
    human_note: str | None
    input_tokens: int
    output_tokens: int
    api_cost: float
    sync_status: str
    created_at: datetime
    confirmed_at: datetime | None


class BatchScreeningOut(BaseModel):
    job_description_id: int
    assessments: list[ScreeningAssessmentOut]


class LoginRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = Field(default=None, min_length=2, max_length=80, pattern=r".*\S.*")


class LoginOut(BaseModel):
    access_token: str
    role: Literal["hr", "department"]
    display_name: str


class AiModelSettingsOut(BaseModel):
    model: str
    provider: str
    base_url: str
    api_key_configured: bool


class AiModelSettingsUpdate(BaseModel):
    model: str = Field(min_length=3, max_length=160, pattern=r"^[A-Za-z0-9._:/-]+$")


class IntegrationSettingsOut(BaseModel):
    tencent_docs_configured: bool
    tencent_docs_file_id: str | None
    tencent_docs_url: str | None
    tencent_docs_sync_mode: Literal["automatic_on_change"] = "automatic_on_change"
    last_tencent_docs_sync_at: datetime | None
    wecom_configured: bool
    wecom_mode: Literal["automatic_after_screening"] = "automatic_after_screening"
    public_app_url: str


class RecruitmentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    candidate_id: int | None
    actor: str
    old_stage: str | None
    new_stage: str | None
    note: str | None
    created_at: datetime


class MetricsOut(BaseModel):
    total_candidates: int
    new_this_week: int
    pending_screening: int
    pending_interview_schedule: int
    pending_feedback: int
    overdue: int
    offers: int
    pending_agent_confirmation: int = 0
    screening_pass_rate: float = 0.0
    average_screening_hours: float = 0.0


class ChartPoint(BaseModel):
    name: str
    value: int | float


class DashboardTrendsOut(BaseModel):
    recent_seven_days: list[ChartPoint]
    position_counts: list[ChartPoint]
    stage_distribution: list[ChartPoint]
    average_stage_hours: list[ChartPoint]


class TaskOut(BaseModel):
    candidate_id: int
    candidate_name: str | None
    stage: str
    department: str | None
    overdue_hours: float
    reminder_text: str


class NotificationOut(BaseModel):
    candidate_id: int
    channel: str
    status: str
    payload: dict


class CsvExportOut(BaseModel):
    path: str
    rows: int
    synced_at: datetime


class TencentDocsSyncOut(BaseModel):
    file_id: str
    url: str
    rows: int
    synced_at: datetime
