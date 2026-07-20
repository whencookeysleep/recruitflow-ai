import argparse
import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from app.config import Settings
from app.database import SessionLocal, create_all
from app.demo_data import CANDIDATES, DEMO_JDS, job_payload
from app.models import Candidate, JobDescription, ResumeFile
from app.schemas import JobDescriptionCreate
from app.services.events import log_event
from app.services.export import TencentDocsSyncAdapter
from app.services.jobs import create_job_description
from scripts.generate_demo_resumes import generate_resumes


def extracted_resume_text(candidate: dict[str, str]) -> str:
    return "\n".join(
        [
            f"姓名：{candidate['name']}",
            "虚构演示候选人 - 仅用于 RecruitFlow AI 面试作业",
            f"应聘岗位：{candidate['position']}",
            f"意向部门：{candidate['department']}",
            f"电话：{candidate['phone']}",
            f"邮箱：{candidate['email']}",
            f"学校：{candidate['school']}",
            f"学历：{candidate['degree']}",
            f"专业：{candidate['major']}",
            f"毕业时间：{candidate['graduation']}",
            f"专业技能：{candidate['skills']}",
            f"实习经历：{candidate['experience']}",
            f"项目经历：{candidate['project']}",
            "所有姓名、联系方式、学校与经历均为虚构数据。",
        ]
    )


def seed_jobs(db) -> int:
    created = 0
    for definition in DEMO_JDS:
        payload = JobDescriptionCreate.model_validate(job_payload(definition))
        existing = db.scalar(
            select(JobDescription).where(
                JobDescription.job_code == payload.job_code,
                JobDescription.version == payload.version,
            )
        )
        if existing is None:
            create_job_description(db, payload)
            created += 1
            continue
        existing.title = payload.jd.title
        existing.department = payload.jd.department
        existing.status = payload.status
        existing.content = payload.jd.model_dump(mode="json")
        existing.created_by = payload.created_by
    db.commit()
    return created


def seed_candidates(db, paths: list[Path]) -> int:
    path_by_slug = {path.stem.removeprefix("demo-resume-"): path for path in paths}
    created = 0
    for profile in CANDIDATES:
        resume_path = path_by_slug[profile["slug"]]
        digest = hashlib.sha256(resume_path.read_bytes()).hexdigest()
        candidate = db.scalar(select(Candidate).where(Candidate.phone == profile["phone"]))
        if candidate is None:
            candidate = Candidate(
                current_stage="待用人部门二筛",
                current_status="active",
                resume_source="虚构 Demo PDF",
                hr_owner="HR Demo",
            )
            db.add(candidate)
            db.flush()
            log_event(
                db,
                "demo_candidate_seeded",
                candidate_id=candidate.id,
                actor="Demo Dataset Seeder",
                new_stage="待用人部门二筛",
                note="创建虚构候选人演示数据",
            )
            created += 1

        candidate.name = profile["name"]
        candidate.phone = profile["phone"]
        candidate.email = profile["email"]
        candidate.school = profile["school"]
        candidate.major = profile["major"]
        candidate.degree = profile["degree"]
        candidate.graduation_date = profile["graduation"]
        candidate.applied_position = profile["position"]
        candidate.department = profile["department"]
        candidate.resume_file_path = str(resume_path)
        candidate.resume_sha256 = digest
        candidate.ai_summary = f"虚构 Demo 候选人，目标岗位为{profile['position']}。"
        candidate.skills = [skill.strip() for skill in profile["skills"].split("、")]
        candidate.matching_points = []
        candidate.risk_points = []
        candidate.interview_questions = []
        candidate.confidence = 1.0

        parsed_payload = {
            "name": profile["name"],
            "phone": profile["phone"],
            "email": profile["email"],
            "school": profile["school"],
            "degree": profile["degree"],
            "major": profile["major"],
            "graduation_date": profile["graduation"],
            "applied_position": profile["position"],
            "skills": candidate.skills,
            "internship_experience": [profile["experience"]],
            "project_experience": [profile["project"]],
            "summary": candidate.ai_summary,
            "confidence": 1.0,
        }
        resume = db.scalar(select(ResumeFile).where(ResumeFile.candidate_id == candidate.id))
        if resume is None:
            resume = ResumeFile(candidate_id=candidate.id)
            db.add(resume)
        resume.filename = resume_path.name
        resume.file_path = str(resume_path)
        resume.sha256 = digest
        resume.extracted_text = extracted_resume_text(profile)
        resume.parse_status = "confirmed"
        resume.parsed_payload = parsed_payload
    db.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the deterministic RecruitFlow AI demo dataset")
    parser.add_argument("--sync-tencent-docs", action="store_true")
    args = parser.parse_args()

    create_all()
    paths = generate_resumes()
    with SessionLocal() as db:
        jobs_created = seed_jobs(db)
        candidates_created = seed_candidates(db, paths)
        result: dict[str, object] = {
            "job_descriptions": db.query(JobDescription).count(),
            "job_descriptions_created": jobs_created,
            "candidates": db.query(Candidate).count(),
            "candidates_created": candidates_created,
            "resume_pdfs": len(paths),
        }
        if args.sync_tencent_docs:
            sync = TencentDocsSyncAdapter().sync_candidates(db, Settings())
            result["tencent_docs_file_id"] = sync.file_id
            result["tencent_docs_rows"] = sync.rows
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
