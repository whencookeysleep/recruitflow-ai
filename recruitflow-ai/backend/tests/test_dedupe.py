from app.models import Candidate
from app.schemas import ParsedResume
from app.services.dedupe import find_duplicate_candidate


def test_candidate_dedupe_matches_same_name_and_reliable_phone(db) -> None:
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
        ParsedResume(name="王测试", phone="13900000000", applied_position="AI 产品经理"),
        "abc",
    )

    assert duplicate is not None
    assert duplicate.id == candidate.id


def test_dedupe_does_not_match_different_names(db) -> None:
    db.add(
        Candidate(
            name="张子轩",
            phone="13900000000",
            email="shared@example.com",
            current_status="active",
        )
    )
    db.commit()

    duplicate = find_duplicate_candidate(
        db,
        ParsedResume(name="周婉清", phone="13900000000", email="shared@example.com"),
        "different-sha",
    )

    assert duplicate is None


def test_dedupe_ignores_masked_phone_and_placeholder_email(db) -> None:
    db.add(
        Candidate(
            name="同名候选人",
            phone="138****8888",
            email="candidate@example.com",
            current_status="active",
        )
    )
    db.commit()

    duplicate = find_duplicate_candidate(
        db,
        ParsedResume(name="同名候选人", phone="138****8888", email="candidate@example.com"),
        "different-sha",
    )

    assert duplicate is None
