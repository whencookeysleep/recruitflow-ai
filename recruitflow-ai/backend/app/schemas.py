from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
