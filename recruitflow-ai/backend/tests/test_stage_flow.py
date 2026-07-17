from app.models import Candidate
from app.services.candidates import apply_screening_result, update_stage


def test_stage_transition_and_screening_result(db) -> None:
    candidate = Candidate(name="赵产品", current_stage="待用人部门二筛", current_status="active")
    db.add(candidate)
    db.commit()

    apply_screening_result(db, candidate, "pass", actor="HR")

    assert candidate.current_stage == "待约面试"

    update_stage(db, candidate, "已约面试", actor="HR")

    assert candidate.current_stage == "已约面试"
