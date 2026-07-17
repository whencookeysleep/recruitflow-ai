from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Candidate, ResumeFile
from app.schemas import CandidateConfirmRequest, ParsedResume
from app.services.ai import parse_resume
from app.services.dedupe import find_duplicate_candidate
from app.services.events import log_event
from app.services.files import copy_to_upload_dir, extract_pdf_text, sha256_file, wait_for_stable_file


def ingest_pdf(db: Session, source_path: Path, settings: Settings, *, copy_file: bool = True) -> ResumeFile:
    if source_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF resumes are supported")
    wait_for_stable_file(source_path)
    stored_path = copy_to_upload_dir(source_path, settings.upload_dir) if copy_file else source_path
    sha256 = sha256_file(stored_path)
    existing = db.scalar(select(ResumeFile).where(ResumeFile.sha256 == sha256))
    if existing:
        log_event(db, "resume_duplicate_file", note=f"Duplicate file ignored: {stored_path.name}")
        db.commit()
        return existing

    text = extract_pdf_text(stored_path)
    resume = ResumeFile(filename=stored_path.name, file_path=str(stored_path), sha256=sha256, extracted_text=text)
    db.add(resume)
    db.flush()
    log_event(db, "resume_discovered", note=f"Resume file discovered: {stored_path.name}")
    parsed = parse_resume_record(db, resume, settings)
    db.refresh(parsed)
    db.commit()
    db.refresh(parsed)
    return parsed


def parse_resume_record(db: Session, resume: ResumeFile, settings: Settings) -> ResumeFile:
    parsed = parse_resume(resume.extracted_text, settings)
    duplicate = find_duplicate_candidate(db, parsed, resume.sha256)
    resume.parsed_payload = parsed.model_dump(mode="json")
    resume.parse_status = "possible_duplicate" if duplicate else "pending_confirmation"
    resume.duplicate_candidate_id = duplicate.id if duplicate else None
    log_event(
        db,
        "ai_parse_success",
        note=f"AI parse completed for {resume.filename}; status={resume.parse_status}",
    )
    return resume


def parsed_to_confirm_request(parsed: ParsedResume) -> CandidateConfirmRequest:
    return CandidateConfirmRequest(
        name=parsed.name,
        phone=parsed.phone,
        email=parsed.email,
        school=parsed.school,
        major=parsed.major,
        degree=parsed.degree,
        graduation_date=parsed.graduation_date,
        applied_position=parsed.applied_position,
        ai_summary=parsed.summary,
        skills=parsed.skills,
        matching_points=parsed.matching_points,
        risk_points=parsed.risk_points,
        interview_questions=parsed.interview_questions,
        confidence=parsed.confidence,
    )


def confirm_resume(db: Session, resume: ResumeFile, request: CandidateConfirmRequest) -> Candidate:
    if resume.parse_status == "confirmed":
        raise ValueError("Resume has already been confirmed")
    if resume.duplicate_candidate_id and not request.create_new_if_duplicate:
        raise ValueError("Possible duplicate requires explicit create_new_if_duplicate=true")

    candidate = Candidate(
        name=request.name,
        phone=request.phone,
        email=str(request.email) if request.email else None,
        school=request.school,
        major=request.major,
        degree=request.degree,
        graduation_date=request.graduation_date,
        applied_position=request.applied_position,
        department=request.department or "AI 平台部",
        hr_owner=request.hr_owner or "HR Demo",
        interviewer=request.interviewer,
        interview_time=request.interview_time,
        current_stage="待用人部门二筛",
        current_status="active",
        resume_file_path=resume.file_path,
        resume_sha256=resume.sha256,
        ai_summary=request.ai_summary,
        skills=request.skills,
        matching_points=request.matching_points,
        risk_points=request.risk_points,
        interview_questions=request.interview_questions,
        confidence=request.confidence,
    )
    db.add(candidate)
    db.flush()
    resume.candidate_id = candidate.id
    resume.parse_status = "confirmed"
    log_event(db, "human_confirmed", candidate_id=candidate.id, actor="HR", new_stage=candidate.current_stage)
    db.commit()
    db.refresh(candidate)
    return candidate
