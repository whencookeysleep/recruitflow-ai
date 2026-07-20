from pathlib import Path

from sqlalchemy.orm import Session

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
