import csv
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Candidate, SystemSetting
from app.schemas import CsvExportOut


class DocumentSyncAdapter:
    def export_candidates(self, db: Session, settings: Settings) -> CsvExportOut:
        raise NotImplementedError


class CSVSyncAdapter(DocumentSyncAdapter):
    def export_candidates(self, db: Session, settings: Settings) -> CsvExportOut:
        settings.export_dir.mkdir(parents=True, exist_ok=True)
        path = settings.export_dir / f"candidates-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
        candidates = list(db.scalars(select(Candidate).where(Candidate.current_status == "active")).all())
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["id", "name", "phone", "email", "school", "major", "degree", "applied_position", "stage", "hr_owner"],
            )
            writer.writeheader()
            for candidate in candidates:
                writer.writerow(
                    {
                        "id": candidate.id,
                        "name": candidate.name,
                        "phone": candidate.phone,
                        "email": candidate.email,
                        "school": candidate.school,
                        "major": candidate.major,
                        "degree": candidate.degree,
                        "applied_position": candidate.applied_position,
                        "stage": candidate.current_stage,
                        "hr_owner": candidate.hr_owner,
                    }
                )
        synced_at = datetime.now(timezone.utc)
        db.merge(SystemSetting(key="last_csv_sync_at", value=synced_at.isoformat()))
        db.commit()
        return CsvExportOut(path=str(path), rows=len(candidates), synced_at=synced_at)


class MockTencentDocAdapter(DocumentSyncAdapter):
    def export_candidates(self, db: Session, settings: Settings) -> CsvExportOut:
        return CSVSyncAdapter().export_candidates(db, settings)
