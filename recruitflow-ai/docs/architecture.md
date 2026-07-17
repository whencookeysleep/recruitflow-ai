# Architecture

```mermaid
flowchart TB
  UI["Next.js Frontend"] --> API["FastAPI API"]
  API --> DB[("SQLite")]
  API --> PDF["PyMuPDF Text Extraction"]
  API --> AI["AI Parser: Mock or OpenAI-compatible"]
  API --> Notify["NotificationAdapter"]
  API --> Sync["DocumentSyncAdapter"]
  Watcher["watchdog resume_inbox watcher"] --> API
```

## Boundaries

- Parsing stays in backend resume services.
- AI is limited to structured extraction and generated summaries.
- Recruitment stage transitions are deterministic application rules.
- Notification and document sync are adapter-based integrations.

## Recruitment Flow

```mermaid
sequenceDiagram
  actor HR
  participant Inbox as resume_inbox / Upload
  participant API as FastAPI
  participant AI as AI Parser
  participant DB as SQLite
  participant Dept as WeCom Adapter

  HR->>Inbox: Download or upload authorized PDF
  Inbox->>API: New PDF event
  API->>API: Wait for stable file and calculate SHA256
  API->>API: Extract PDF text
  API->>AI: Structured resume parsing
  AI-->>API: Pydantic-validated JSON
  API->>DB: Store pending resume and event
  HR->>API: Confirm or edit parsed fields
  API->>DB: Create confirmed candidate
  HR->>Dept: Send screening card
  HR->>API: Mark screening passed
  API->>DB: Move stage to 待约面试 and log event
```

## Data Model

- `candidates`: confirmed and active candidate records.
- `resume_files`: uploaded or discovered resume files and AI parsing payloads.
- `recruitment_events`: audit trail for ingestion, parsing, confirmation, stage changes, notifications, and export.
- `interview_records`: interview schedule and feedback.
- `notification_logs`: mock or real WeCom send logs.
- `system_settings`: small operational settings such as last CSV sync time.
