from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models import Candidate, ResumeFile
from app.schemas import CandidateConfirmRequest
from app.services import resumes


def test_ingest_pdf_persists_parsed_payload_before_refresh(
    db: Session, tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "resume.pdf"
    source.write_bytes(b"demo")

    monkeypatch.setattr(resumes, "wait_for_stable_file", lambda path: None)
    monkeypatch.setattr(resumes, "sha256_file", lambda path: "demo-sha")
    monkeypatch.setattr(resumes, "extract_pdf_text", lambda path: "demo resume")

    def parse_record(session, resume, settings):
        resume.parsed_payload = {"name": "Demo Candidate"}
        resume.parse_status = "pending_confirmation"
        return resume

    monkeypatch.setattr(resumes, "parse_resume_record", parse_record)

    result = resumes.ingest_pdf(db, source, object(), copy_file=False)

    assert result.parsed_payload == {"name": "Demo Candidate"}
    db.expire_all()
    assert db.get(type(result), result.id).parsed_payload == {"name": "Demo Candidate"}


def test_ingest_pdf_reparses_existing_incomplete_record(
    db: Session, tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "resume.pdf"
    source.write_bytes(b"demo")

    monkeypatch.setattr(resumes, "wait_for_stable_file", lambda path: None)
    monkeypatch.setattr(resumes, "sha256_file", lambda path: "demo-sha")
    monkeypatch.setattr(resumes, "extract_pdf_text", lambda path: "demo resume")

    calls = 0

    def parse_record(session, resume, settings):
        nonlocal calls
        calls += 1
        resume.parsed_payload = {"name": "Demo Candidate"}
        resume.parse_status = "pending_confirmation"
        return resume

    monkeypatch.setattr(resumes, "parse_resume_record", parse_record)

    first = resumes.ingest_pdf(db, source, object(), copy_file=False)
    first.parsed_payload = None
    db.commit()

    second = resumes.ingest_pdf(db, source, object(), copy_file=False)

    assert calls == 2
    assert second.id == first.id
    assert second.parsed_payload == {"name": "Demo Candidate"}


def test_confirm_links_same_name_duplicate(db: Session) -> None:
    candidate = Candidate(name="同名候选人", current_status="active")
    db.add(candidate)
    db.flush()
    resume = ResumeFile(
        filename="resume.pdf",
        file_path="resume.pdf",
        sha256="new-sha",
        parse_status="possible_duplicate",
        parsed_payload={"name": "同名候选人"},
        duplicate_candidate_id=candidate.id,
    )
    db.add(resume)
    db.commit()

    result = resumes.confirm_resume(db, resume, CandidateConfirmRequest(name="同名候选人"))

    assert result.id == candidate.id
    assert resume.candidate_id == candidate.id
    assert resume.parse_status == "confirmed"


def test_confirm_creates_new_candidate_when_duplicate_name_differs(db: Session) -> None:
    candidate = Candidate(name="已有候选人", current_status="active")
    db.add(candidate)
    db.flush()
    resume = ResumeFile(
        filename="resume.pdf",
        file_path="resume.pdf",
        sha256="new-sha",
        parse_status="possible_duplicate",
        parsed_payload={"name": "新候选人"},
        duplicate_candidate_id=candidate.id,
    )
    db.add(resume)
    db.commit()

    result = resumes.confirm_resume(db, resume, CandidateConfirmRequest(name="新候选人"))

    assert result.id != candidate.id
    assert result.name == "新候选人"
    assert resume.candidate_id == result.id
    assert resume.duplicate_candidate_id is None


def test_link_duplicate_rejects_different_name(db: Session) -> None:
    candidate = Candidate(name="已有候选人", current_status="active")
    db.add(candidate)
    db.flush()
    resume = ResumeFile(
        filename="resume.pdf",
        file_path="resume.pdf",
        sha256="new-sha",
        parse_status="possible_duplicate",
        parsed_payload={"name": "新候选人"},
        duplicate_candidate_id=candidate.id,
    )
    db.add(resume)
    db.commit()

    with pytest.raises(ValueError, match="same candidate name"):
        resumes.link_duplicate_resume(db, resume)
