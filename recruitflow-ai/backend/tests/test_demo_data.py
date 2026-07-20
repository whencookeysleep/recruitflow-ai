from collections import Counter

from app.demo_data import CANDIDATES, DEMO_JDS, job_payload
from app.schemas import JobDescriptionCreate


def test_demo_dataset_has_seven_valid_jobs_and_fifty_unique_candidates() -> None:
    validated_jobs = [JobDescriptionCreate.model_validate(job_payload(job)) for job in DEMO_JDS]

    assert len(validated_jobs) == 7
    assert len({job.jd.department for job in validated_jobs}) == 7
    assert len(CANDIDATES) == 50
    assert len({candidate["phone"] for candidate in CANDIDATES}) == 50
    assert len({candidate["email"] for candidate in CANDIDATES}) == 50


def test_demo_dataset_contains_overlapping_roles_and_mismatched_profiles() -> None:
    role_counts = Counter(candidate["position"] for candidate in CANDIDATES)
    match_counts = Counter(candidate["profile_match"] for candidate in CANDIDATES)

    assert len(role_counts) == 7
    assert all(count >= 7 for count in role_counts.values())
    assert match_counts == {"matched": 30, "adjacent": 10, "mismatched": 10}
