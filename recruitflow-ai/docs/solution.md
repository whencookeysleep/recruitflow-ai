# RecruitFlow AI Solution

RecruitFlow AI is a non-invasive HR automation demo. It starts from files that HR manually downloads and uses AI only where unstructured resume understanding creates value.

## Cost Principle

该方案采用“该花花、该省省”的成本原则：人工保留在 BOSS 初筛、下载和关键招聘决策处；自动化覆盖下载后的录入、解析、转发、状态提醒和统计；大模型只用于简历理解、摘要和可选日报。

## Product Boundaries

- No BOSS login credentials are stored.
- No BOSS page scraping or unauthorized bulk download is implemented.
- Local PDF files and web uploads are the only ingestion paths.
- AI output is stored as pending data until a human confirms it.
- Stage transitions, overdue checks, dashboard metrics, and CSV export are deterministic program rules.

## AI Mode

`AI_PROVIDER=mock` is the default and requires no key. For OpenAI-compatible mode, set `AI_PROVIDER=openai`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL`. The parser validates model output through Pydantic before the result can enter the confirmation queue.

## Adapter Strategy

- `NotificationAdapter` supports `MockWeComAdapter` and `WeComWebhookAdapter`.
- `CSVSyncAdapter` provides local export; `TencentDocsSyncAdapter` sends incremental candidate versions through the official Tencent Docs MCP endpoint.
- Both integration points are replaceable without changing candidate workflow code.
