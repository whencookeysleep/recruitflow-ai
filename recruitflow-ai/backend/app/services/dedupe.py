from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import Candidate
from app.schemas import ParsedResume


def _normalized_name(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = "".join(value.split()).casefold()
    return normalized or None


def _is_reliable_phone(value: str | None) -> bool:
    return bool(value and "*" not in value and sum(character.isdigit() for character in value) >= 7)


def _is_reliable_email(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().casefold()
    return normalized not in {"candidate@example.com", "example@example.com"}


def _same_name(candidate: Candidate, parsed: ParsedResume) -> bool:
    parsed_name = _normalized_name(parsed.name)
    return parsed_name is not None and _normalized_name(candidate.name) == parsed_name


def find_duplicate_candidate(db: Session, parsed: ParsedResume, sha256: str) -> Candidate | None:
    if _is_reliable_phone(parsed.phone):
        candidate = db.scalar(select(Candidate).where(Candidate.phone == parsed.phone))
        if candidate and _same_name(candidate, parsed):
            return candidate
    if _is_reliable_email(str(parsed.email) if parsed.email else None):
        candidate = db.scalar(select(Candidate).where(Candidate.email == str(parsed.email)))
        if candidate and _same_name(candidate, parsed):
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
    candidate = db.scalar(select(Candidate).where(Candidate.resume_sha256 == sha256))
    return candidate if candidate and _same_name(candidate, parsed) else None
