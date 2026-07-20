from pathlib import Path

from app.config import Settings
from app.models import Candidate
import pytest

from app.services.export import CSVSyncAdapter, TencentDocsSyncAdapter


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


class FakeTencentDocsClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": "manage.create_file",
                "inputSchema": {
                    "type": "object",
                    "properties": {"title": {}, "file_type": {}},
                },
            },
            {
                "name": "sheet.get_sheet_info",
                "inputSchema": {"type": "object", "properties": {"file_id": {}}},
            },
            {
                "name": "manage.query_file_info",
                "inputSchema": {"type": "object", "properties": {"file_id": {}}},
            },
            {
                "name": "sheet.set_range_value",
                "inputSchema": {
                    "type": "object",
                    "properties": {"file_id": {}, "sheet_id": {}, "values": {}},
                },
            },
        ]

    def call_tool(self, name: str, arguments: dict) -> dict:
        self.calls.append((name, arguments))
        if name == "manage.create_file":
            return {"file_id": "file-1"}
        if name == "sheet.get_sheet_info":
            return {"sheets": [{"sheet_id": "sheet-1", "sheet_type": "worksheet"}]}
        if name == "manage.query_file_info":
            return {"file_id": "file-1", "url": "https://docs.qq.com/sheet/DRmlsZS0x"}
        return {}


def test_tencent_docs_sync_appends_candidate_rows(db) -> None:
    candidate = Candidate(
        name="孙同步",
        phone="13600000000",
        email="sync@example.com",
        applied_position="AI 管培生",
        current_status="active",
    )
    db.add(candidate)
    db.commit()
    client = FakeTencentDocsClient()
    settings = Settings(
        tencent_docs_token="token",
    )

    result = TencentDocsSyncAdapter(client=client).sync_candidates(db, settings)

    assert result.rows == 1
    assert result.url == "https://docs.qq.com/sheet/DRmlsZS0x"
    assert [call[0] for call in client.calls] == [
        "manage.create_file",
        "sheet.get_sheet_info",
        "manage.query_file_info",
        "sheet.set_range_value",
    ]
    arguments = client.calls[3][1]
    assert arguments["file_id"] == "file-1"
    assert arguments["sheet_id"] == "sheet-1"
    assert arguments["values"][0] == {"row": 0, "col": 0, "value_type": "STRING", "string_value": "候选人ID"}
    assert {"row": 1, "col": 1, "value_type": "STRING", "string_value": "孙同步"} in arguments["values"]

    second_result = TencentDocsSyncAdapter(client=client).sync_candidates(db, settings)

    assert second_result.rows == 0
    assert len(client.calls) == 4


def test_targeted_tencent_docs_sync_does_not_advance_global_cursor(db) -> None:
    first = Candidate(name="候选人一", current_status="active")
    second = Candidate(name="候选人二", current_status="active")
    db.add_all([first, second])
    db.commit()
    client = FakeTencentDocsClient()
    settings = Settings(tencent_docs_token="token")

    targeted = TencentDocsSyncAdapter(client=client).sync_candidates(
        db,
        settings,
        candidate_ids=[first.id],
    )
    full = TencentDocsSyncAdapter(client=client).sync_candidates(db, settings)

    assert targeted.rows == 1
    assert full.rows == 2


def test_tencent_docs_sync_requires_explicit_credentials(db) -> None:
    with pytest.raises(ValueError, match="TENCENT_DOCS_TOKEN"):
        TencentDocsSyncAdapter().sync_candidates(db, Settings(tencent_docs_token=None, _env_file=None))
