import csv
import json
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Candidate, JobDescription, ScreeningAssessment, SystemSetting
from app.schemas import CsvExportOut, IntegrationSettingsOut, TencentDocsSyncOut


class DocumentSyncAdapter:
    def export_candidates(self, db: Session, settings: Settings) -> CsvExportOut:
        raise NotImplementedError


class CSVSyncAdapter(DocumentSyncAdapter):
    def export_candidates(self, db: Session, settings: Settings) -> CsvExportOut:
        settings.export_dir.mkdir(parents=True, exist_ok=True)
        path = settings.export_dir / f"candidates-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
        candidates = list(db.scalars(select(Candidate).where(Candidate.current_status == "active")).all())
        assessments = _latest_assessments(db)
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["id", "name", "phone", "email", "school", "major", "degree", "applied_position", "stage", "hr_owner", "job_code", "agent_score", "agent_recommendation", "human_decision"],
            )
            writer.writeheader()
            for candidate in candidates:
                assessment, job = assessments.get(candidate.id, (None, None))
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
                        "job_code": job.job_code if job else None,
                        "agent_score": assessment.total_score if assessment else None,
                        "agent_recommendation": assessment.recommendation if assessment else None,
                        "human_decision": assessment.human_decision if assessment else None,
                    }
                )
        synced_at = datetime.now(timezone.utc)
        db.merge(SystemSetting(key="last_csv_sync_at", value=synced_at.isoformat()))
        db.commit()
        return CsvExportOut(path=str(path), rows=len(candidates), synced_at=synced_at)


class TencentDocsMCPClient:
    def __init__(self, endpoint: str, token: str) -> None:
        self.endpoint = endpoint
        self.headers = {
            "Authorization": token,
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._request("tools/list", {})
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            message = _tool_result_text(result) or f"Tencent Docs tool failed: {name}"
            raise RuntimeError(message)
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
        text = _tool_result_text(result)
        if text:
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
            if isinstance(payload, dict):
                return payload
        return result

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            self.endpoint,
            headers=self.headers,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            timeout=30,
        )
        response.raise_for_status()
        payload = _decode_mcp_response(response)
        if "error" in payload:
            error = payload["error"]
            raise RuntimeError(f"Tencent Docs MCP error {error.get('code')}: {error.get('message')}")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("Tencent Docs MCP returned no result object")
        return result


def _decode_mcp_response(response: httpx.Response) -> dict[str, Any]:
    if "application/json" in response.headers.get("content-type", ""):
        return response.json()
    data_lines = [line[5:].strip() for line in response.text.splitlines() if line.startswith("data:")]
    if not data_lines:
        raise RuntimeError("Tencent Docs MCP returned an unsupported response")
    return json.loads(data_lines[-1])


def _tool_result_text(result: dict[str, Any]) -> str | None:
    for item in result.get("content", []):
        if item.get("type") == "text" and item.get("text"):
            return str(item["text"])
    return None


class TencentDocsSyncAdapter:
    create_file_tool = "manage.create_file"
    query_file_info_tool = "manage.query_file_info"
    get_sheet_info_tool = "sheet.get_sheet_info"
    set_range_value_tool = "sheet.set_range_value"
    file_id_setting = "tencent_docs_file_id"
    sheet_id_setting = "tencent_docs_sheet_id"
    columns = [
        "候选人ID",
        "姓名",
        "电话",
        "邮箱",
        "学校",
        "专业",
        "学历",
        "应聘岗位",
        "招聘阶段",
        "候选人状态",
        "HR负责人",
        "更新时间",
        "JD编号",
        "AI匹配分",
        "Agent建议",
        "人工结论",
    ]

    def __init__(self, client: TencentDocsMCPClient | None = None) -> None:
        self.client = client

    def sync_candidates(
        self,
        db: Session,
        settings: Settings,
        candidate_ids: list[int] | None = None,
    ) -> TencentDocsSyncOut:
        token = settings.tencent_docs_token
        if not token:
            raise ValueError("TENCENT_DOCS_TOKEN is required for Tencent Docs sync")
        if candidate_ids is not None and not candidate_ids:
            raise ValueError("candidate_ids must not be empty when provided")

        client = self.client or TencentDocsMCPClient(settings.tencent_docs_mcp_url, token)
        self._validate_tool_contract(client.list_tools())
        file_id, sheet_id = self._resolve_target(db, settings, client)
        file_url = self._resolve_file_url(db, client, file_id)
        last_sync_key = f"last_tencent_docs_sync_at:{file_id}:{sheet_id}"
        sync_started_at = datetime.now(timezone.utc)
        last_sync = db.get(SystemSetting, last_sync_key)
        query = select(Candidate).where(Candidate.updated_at <= sync_started_at)
        if candidate_ids is not None:
            query = query.where(Candidate.id.in_(set(candidate_ids)))
        elif last_sync and last_sync.value:
            query = query.where(Candidate.updated_at > datetime.fromisoformat(last_sync.value))
        candidates = list(db.scalars(query.order_by(Candidate.updated_at, Candidate.id)).all())
        assessments = _latest_assessments(db)

        values = self._cell_values([self.columns], 0) if candidates or not last_sync else []
        for candidate in candidates:
            assessment, job = assessments.get(candidate.id, (None, None))
            values.extend(self._cell_values([self._candidate_row(candidate, assessment, job)], candidate.id))
        if values:
            client.call_tool(
                self.set_range_value_tool,
                {"file_id": file_id, "sheet_id": sheet_id, "values": values},
            )

        if candidate_ids is None:
            db.merge(SystemSetting(key=last_sync_key, value=sync_started_at.isoformat()))
        db.commit()
        return TencentDocsSyncOut(
            file_id=file_id,
            url=file_url,
            rows=len(candidates),
            synced_at=sync_started_at,
        )

    def _resolve_target(
        self, db: Session, settings: Settings, client: TencentDocsMCPClient
    ) -> tuple[str, str]:
        stored_file_id = db.get(SystemSetting, self.file_id_setting)
        stored_sheet_id = db.get(SystemSetting, self.sheet_id_setting)
        file_id = settings.tencent_docs_file_id or (stored_file_id.value if stored_file_id else None)
        sheet_id = settings.tencent_docs_sheet_id or (stored_sheet_id.value if stored_sheet_id else None)

        if not file_id:
            created = client.call_tool(
                self.create_file_tool,
                {"title": "RecruitFlow AI 招聘数据", "file_type": "sheet"},
            )
            self._raise_tool_error(created)
            file_id = created.get("file_id")
            if not file_id:
                raise RuntimeError("Tencent Docs did not return file_id after creating the sheet")
            db.merge(SystemSetting(key=self.file_id_setting, value=str(file_id)))
            db.commit()

        if not sheet_id:
            sheet_info = client.call_tool(self.get_sheet_info_tool, {"file_id": file_id})
            self._raise_tool_error(sheet_info)
            sheets = sheet_info.get("sheets", [])
            worksheet = next((sheet for sheet in sheets if sheet.get("sheet_type") == "worksheet"), None)
            if not worksheet and sheets:
                worksheet = sheets[0]
            sheet_id = worksheet.get("sheet_id") if worksheet else None
            if not sheet_id:
                raise RuntimeError("Tencent Docs did not return a worksheet ID")
            db.merge(SystemSetting(key=self.sheet_id_setting, value=str(sheet_id)))
            db.commit()

        return str(file_id), str(sheet_id)

    def _resolve_file_url(
        self,
        db: Session,
        client: TencentDocsMCPClient,
        file_id: str,
    ) -> str:
        setting_key = f"tencent_docs_url:{file_id}"
        stored = db.get(SystemSetting, setting_key)
        if stored and stored.value:
            return stored.value

        file_info = client.call_tool(self.query_file_info_tool, {"file_id": file_id})
        self._raise_tool_error(file_info)
        file_url = file_info.get("url")
        if not isinstance(file_url, str) or not file_url.startswith("https://docs.qq.com/"):
            raise RuntimeError("Tencent Docs did not return a valid document URL")
        db.merge(SystemSetting(key=setting_key, value=file_url))
        db.commit()
        return file_url

    def _validate_tool_contract(self, tools: list[dict[str, Any]]) -> None:
        expected = {
            self.create_file_tool: {"title", "file_type"},
            self.query_file_info_tool: {"file_id"},
            self.get_sheet_info_tool: {"file_id"},
            self.set_range_value_tool: {"file_id", "sheet_id", "values"},
        }
        tools_by_name = {item.get("name"): item for item in tools}
        for name, arguments in expected.items():
            tool = tools_by_name.get(name)
            if not tool:
                raise RuntimeError(f"Tencent Docs MCP does not expose {name}")
            properties = set(tool.get("inputSchema", {}).get("properties", {}))
            if not arguments.issubset(properties):
                raise RuntimeError(
                    f"Tencent Docs MCP {name} contract changed; expected {sorted(arguments)}, got {sorted(properties)}"
                )

    @staticmethod
    def _raise_tool_error(result: dict[str, Any]) -> None:
        if result.get("error"):
            raise RuntimeError(str(result["error"]))

    @staticmethod
    def _cell_values(rows: list[list[str | int | float | None]], start_row: int) -> list[dict[str, Any]]:
        cells: list[dict[str, Any]] = []
        for row_offset, row in enumerate(rows):
            for col, value in enumerate(row):
                cell: dict[str, Any] = {
                    "row": start_row + row_offset,
                    "col": col,
                    "value_type": "NUMBER" if isinstance(value, int) else "STRING",
                }
                if isinstance(value, (int, float)):
                    cell["value_type"] = "NUMBER"
                    cell["number_value"] = value
                else:
                    cell["string_value"] = "" if value is None else str(value)
                cells.append(cell)
        return cells


    @staticmethod
    def _candidate_row(
        candidate: Candidate,
        assessment: ScreeningAssessment | None,
        job: JobDescription | None,
    ) -> list[str | int | float | None]:
        return [
            candidate.id,
            candidate.name,
            candidate.phone,
            candidate.email,
            candidate.school,
            candidate.major,
            candidate.degree,
            candidate.applied_position,
            candidate.current_stage,
            candidate.current_status,
            candidate.hr_owner,
            candidate.updated_at.isoformat(),
            job.job_code if job else None,
            assessment.total_score if assessment else None,
            assessment.recommendation if assessment else None,
            assessment.human_decision if assessment else None,
        ]


def _latest_assessments(
    db: Session,
) -> dict[int, tuple[ScreeningAssessment, JobDescription | None]]:
    assessments = list(
        db.scalars(select(ScreeningAssessment).order_by(ScreeningAssessment.created_at.desc())).all()
    )
    latest: dict[int, tuple[ScreeningAssessment, JobDescription | None]] = {}
    for assessment in assessments:
        if assessment.candidate_id in latest:
            continue
        latest[assessment.candidate_id] = (
            assessment,
            db.get(JobDescription, assessment.job_description_id),
        )
    return latest


def integration_settings(db: Session, settings: Settings) -> IntegrationSettingsOut:
    stored_file_id = db.get(SystemSetting, TencentDocsSyncAdapter.file_id_setting)
    stored_sheet_id = db.get(SystemSetting, TencentDocsSyncAdapter.sheet_id_setting)
    file_id = settings.tencent_docs_file_id or (stored_file_id.value if stored_file_id else None)
    sheet_id = settings.tencent_docs_sheet_id or (stored_sheet_id.value if stored_sheet_id else None)
    stored_url = db.get(SystemSetting, f"tencent_docs_url:{file_id}") if file_id else None
    last_sync = (
        db.get(SystemSetting, f"last_tencent_docs_sync_at:{file_id}:{sheet_id}")
        if file_id and sheet_id
        else None
    )
    return IntegrationSettingsOut(
        tencent_docs_configured=bool(settings.tencent_docs_token),
        tencent_docs_file_id=file_id,
        tencent_docs_url=stored_url.value if stored_url and stored_url.value else None,
        last_tencent_docs_sync_at=(
            datetime.fromisoformat(last_sync.value) if last_sync and last_sync.value else None
        ),
        wecom_configured=bool(settings.wecom_webhook_url),
        public_app_url=settings.public_app_url,
    )
