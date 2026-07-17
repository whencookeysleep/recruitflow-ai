from app.models import Candidate
from app.schemas import ParsedResume
from app.services.dedupe import find_duplicate_candidate


def test_candidate_dedupe_prefers_phone(db) -> None:
    candidate = Candidate(
        name="王测试",
        phone="13900000000",
        email="old@example.com",
        school="示例大学",
        applied_position="测试工程师",
        current_status="active",
    )
    db.add(candidate)
    db.commit()

    duplicate = find_duplicate_candidate(
        db,
        ParsedResume(name="其他人", phone="13900000000", applied_position="AI 产品经理"),
        "abc",
    )

    assert duplicate is not None
    assert duplicate.id == candidate.id
