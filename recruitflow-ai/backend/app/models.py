from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


STAGES = [
    "HR 初筛通过",
    "待用人部门二筛",
    "二筛通过",
    "二筛不通过",
    "待约面试",
    "已约面试",
    "面试完成",
    "待面试反馈",
    "面试通过",
    "面试不通过",
    "Offer 待审批",
    "Offer 已发放",
    "已入职",
    "已放弃",
]


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(64), index=True)
    email: Mapped[str | None] = mapped_column(String(160), index=True)
    school: Mapped[str | None] = mapped_column(String(160))
    major: Mapped[str | None] = mapped_column(String(160))
    degree: Mapped[str | None] = mapped_column(String(80))
    graduation_date: Mapped[str | None] = mapped_column(String(80))
    applied_position: Mapped[str | None] = mapped_column(String(160), index=True)
    resume_source: Mapped[str] = mapped_column(String(80), default="BOSS 下载 PDF")
    current_stage: Mapped[str] = mapped_column(String(80), default="HR 初筛通过", index=True)
    department: Mapped[str | None] = mapped_column(String(120))
    hr_owner: Mapped[str | None] = mapped_column(String(120), index=True)
    interviewer: Mapped[str | None] = mapped_column(String(120))
    interview_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_status: Mapped[str] = mapped_column(String(80), default="pending_confirmation", index=True)
    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False)
    resume_file_path: Mapped[str | None] = mapped_column(String(500))
    resume_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    matching_points: Mapped[list[str]] = mapped_column(JSON, default=list)
    risk_points: Mapped[list[str]] = mapped_column(JSON, default=list)
    interview_questions: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    resume_files: Mapped[list["ResumeFile"]] = relationship(foreign_keys="ResumeFile.candidate_id", back_populates="candidate")
    events: Mapped[list["RecruitmentEvent"]] = relationship(back_populates="candidate")
    screening_assessments: Mapped[list["ScreeningAssessment"]] = relationship(back_populates="candidate")


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    __table_args__ = (UniqueConstraint("job_code", "version", name="uq_job_description_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_code: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(160), index=True)
    department: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    content: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    screening_assessments: Mapped[list["ScreeningAssessment"]] = relationship(back_populates="job_description")


class ScreeningAssessment(Base):
    __tablename__ = "screening_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id"), index=True)
    job_description_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id"), index=True)
    recommendation: Mapped[str] = mapped_column(String(40), index=True)
    total_score: Mapped[float] = mapped_column(Float)
    criteria_results: Mapped[list[dict]] = mapped_column(JSON, default=list)
    hard_requirement_failures: Mapped[list[str]] = mapped_column(JSON, default=list)
    risk_points: Mapped[list[str]] = mapped_column(JSON, default=list)
    interview_questions: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(160))
    prompt_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="agent_recommended", index=True)
    human_decision: Mapped[str | None] = mapped_column(String(40))
    human_actor: Mapped[str | None] = mapped_column(String(120))
    human_username: Mapped[str | None] = mapped_column(String(120))
    human_role: Mapped[str | None] = mapped_column(String(40))
    human_note: Mapped[str | None] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    api_cost: Mapped[float] = mapped_column(Float, default=0.0)
    sync_status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    candidate: Mapped[Candidate] = relationship(back_populates="screening_assessments")
    job_description: Mapped[JobDescription] = relationship(back_populates="screening_assessments")


class ResumeFile(Base):
    __tablename__ = "resume_files"
    __table_args__ = (UniqueConstraint("sha256", name="uq_resume_files_sha256"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    parse_status: Mapped[str] = mapped_column(String(80), default="pending_confirmation", index=True)
    parsed_payload: Mapped[dict | None] = mapped_column(JSON)
    duplicate_candidate_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("candidates.id"))
    candidate_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("candidates.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    candidate: Mapped[Candidate | None] = relationship(foreign_keys=[candidate_id], back_populates="resume_files")
    duplicate_candidate: Mapped[Candidate | None] = relationship(foreign_keys=[duplicate_candidate_id])

    @property
    def duplicate_reason(self) -> str | None:
        candidate = self.duplicate_candidate
        payload = self.parsed_payload or {}
        if candidate is None:
            return None
        phone = payload.get("phone")
        if isinstance(phone, str) and "*" not in phone and phone == candidate.phone:
            return "phone"
        email = payload.get("email")
        if isinstance(email, str) and email.casefold() not in {"candidate@example.com", "example@example.com"} and email == candidate.email:
            return "email"
        if self.sha256 == candidate.resume_sha256:
            return "resume_sha256"
        return "name_school_position"


class RecruitmentEvent(Base):
    __tablename__ = "recruitment_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    candidate_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("candidates.id"))
    actor: Mapped[str] = mapped_column(String(120), default="system")
    old_stage: Mapped[str | None] = mapped_column(String(80))
    new_stage: Mapped[str | None] = mapped_column(String(80))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    candidate: Mapped[Candidate | None] = relationship(back_populates="events")


class InterviewRecord(Base):
    __tablename__ = "interview_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidates.id"), index=True)
    interviewer: Mapped[str | None] = mapped_column(String(120))
    interview_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    feedback: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("candidates.id"), index=True)
    channel: Mapped[str] = mapped_column(String(80), default="mock_wecom")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80), default="sent")
    response: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(160), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
