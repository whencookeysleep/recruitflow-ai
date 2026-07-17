# API Reference

The API is served by FastAPI. Detailed OpenAPI documentation is available at `/docs` when the backend is running.

## Health

- `GET /api/health`

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
- `POST /api/candidates/{id}/send-screening-card` sends or mocks a WeCom screening card.

## Dashboard And Operations

- `GET /api/dashboard/metrics`
- `GET /api/dashboard/funnel`
- `GET /api/dashboard/trends`
- `GET /api/tasks`
- `GET /api/events`
- `POST /api/export/csv`
