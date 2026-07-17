from pathlib import Path

from app.config import Settings
from app.models import Candidate
from app.services.export import CSVSyncAdapter


def test_csv_export(tmp_path: Path, db) -> None:
    db.add(
        Candidate(
            name="孙导出",
            phone="13700000000",
            email="export@example.com",
            school="示例大学",
            applied_position="AI 管培生",
            current_status="active",
        )
    )
    db.commit()
    settings = Settings(export_dir=tmp_path, upload_dir=tmp_path, resume_inbox_dir=tmp_path)

    result = CSVSyncAdapter().export_candidates(db, settings)

    assert result.rows == 1
    assert Path(result.path).exists()
    assert "孙导出" in Path(result.path).read_text(encoding="utf-8-sig")
