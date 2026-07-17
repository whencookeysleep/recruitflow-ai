from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import Candidate
from app.schemas import ParsedResume


def find_duplicate_candidate(db: Session, parsed: ParsedResume, sha256: str) -> Candidate | None:
    if parsed.phone:
        candidate = db.scalar(select(Candidate).where(Candidate.phone == parsed.phone))
        if candidate:
            return candidate
    if parsed.email:
        candidate = db.scalar(select(Candidate).where(Candidate.email == str(parsed.email)))
        if candidate:
            return candidate
    if parsed.name and parsed.school and parsed.applied_position:
        candidate = db.scalar(
            select(Candidate).where(
                and_(
                    Candidate.name == parsed.name,
                    Candidate.school == parsed.school,
                    Candidate.applied_position == parsed.applied_position,
                )
            )
        )
        if candidate:
            return candidate
    return db.scalar(select(Candidate).where(Candidate.resume_sha256 == sha256))
