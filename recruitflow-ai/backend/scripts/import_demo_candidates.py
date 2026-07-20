import json
from pathlib import Path

from app.config import Settings
from app.database import SessionLocal, create_all
from app.models import Candidate
from app.schemas import ParsedResume
from app.services.export import TencentDocsSyncAdapter
from app.services.resumes import confirm_resume, ingest_pdf, parsed_to_confirm_request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESUME_DIR = PROJECT_ROOT / "output" / "pdf"


def main() -> None:
    settings = Settings()
    if settings.ai_provider == "mock":
        raise RuntimeError("AI_PROVIDER must not be mock when importing AI-parsed demo candidates")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    resume_paths = sorted(RESUME_DIR.glob("demo-resume-*.pdf"))
    if not resume_paths:
        raise RuntimeError(f"No demo resume PDFs found in {RESUME_DIR}")

    create_all()
    imported: list[dict[str, object]] = []
    with SessionLocal() as db:
        for resume_path in resume_paths:
            resume = ingest_pdf(db, resume_path, settings, copy_file=True)
            if resume.parse_status == "confirmed" and resume.candidate_id:
                candidate = db.get(Candidate, resume.candidate_id)
                if candidate is None:
                    raise RuntimeError(
                        f"Resume {resume.filename} references missing candidate {resume.candidate_id}"
                    )
                action = "existing"
            else:
                if not resume.parsed_payload:
                    raise RuntimeError(f"Resume {resume.filename} has no parsed AI payload")
                parsed = ParsedResume.model_validate(resume.parsed_payload)
                request = parsed_to_confirm_request(parsed)
                candidate = confirm_resume(db, resume, request)
                action = "created"

            imported.append(
                {
                    "action": action,
                    "candidate_id": candidate.id,
                    "name": candidate.name,
                    "position": candidate.applied_position,
                }
            )

        sync_result = TencentDocsSyncAdapter().sync_candidates(db, settings)

    print(json.dumps({"candidates": imported}, ensure_ascii=True, indent=2))
    print(
        json.dumps(
            {
                "tencent_docs_file_id": sync_result.file_id,
                "rows_synced": sync_result.rows,
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
