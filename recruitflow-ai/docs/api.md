# API Reference

The API is served by FastAPI. Detailed OpenAPI documentation is available at `/docs` when the backend is running.

## Health

- `GET /api/health`

## Authentication

- `POST /api/auth/login` returns a signed, expiring access token.
- Protected endpoints require `Authorization: Bearer <token>`.
- HR and department roles are enforced separately.

## Job Descriptions And Agent Screening

- `POST /api/job-descriptions` validates and versions a department-owned JD JSON document.
- `GET /api/job-descriptions` lists JD versions, optionally filtered by status.
- `PATCH /api/job-descriptions/{id}` updates a JD or its lifecycle status.
- `POST /api/candidates/{id}/agent-screen` runs evidence-grounded DeepSeek screening without changing recruitment stage.
- `POST /api/job-descriptions/{id}/screen-pending` screens selected candidates or all matching pending candidates.
- `GET /api/candidates/{id}/assessments` returns auditable Agent runs.
- `POST /api/screening-assessments/{id}/confirm` records the department decision, updates stage, and synchronizes Tencent Docs.

## Resumes

- `POST /api/resumes/upload` uploads an authorized PDF and creates a pending confirmation record.
- `POST /api/resumes/{id}/parse` reruns AI parsing for a stored resume.
- `POST /api/resumes/{id}/confirm` confirms parsed data into the formal candidate table.
- `GET /api/resumes/pending` lists resumes waiting for human confirmation or duplicate review.

## Candidates

- `GET /api/candidates` lists confirmed candidates with optional `search`, `position`, `stage`, and `owner` filters.
- `GET /api/candidates/{id}` returns one candidate.
- `PATCH /api/candidates/{id}` updates editable fields.
- `PATCH /api/candidates/{id}/stage` updates recruitment stage with event logging.
- `GET /api/candidates/{id}/events` returns the candidate event history.
- `POST /api/candidates/{id}/screening-result` records pass, reject, or hold. `pass` moves the candidate to `待约面试`.
- `POST /api/candidates/{id}/send-screening-card?assessment_id={assessment_id}` sends or mocks a WeCom card containing Agent score, evidence and a confirmation link.

## Dashboard And Operations

- `GET /api/dashboard/metrics`
- `GET /api/dashboard/funnel`
- `GET /api/dashboard/trends`
- `GET /api/tasks`
- `GET /api/events`
- `POST /api/export/csv`
- `POST /api/export/tencent-docs` incrementally overwrites each candidate's stable row through the official MCP endpoint, including JD code, score, recommendation and human decision.
