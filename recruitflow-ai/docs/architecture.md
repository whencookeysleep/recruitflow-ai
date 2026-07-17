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
