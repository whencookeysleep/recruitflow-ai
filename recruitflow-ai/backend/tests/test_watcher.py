from pathlib import Path
from unittest.mock import Mock

from watchdog.events import FileCreatedEvent, FileMovedEvent

from app.config import Settings
from app.services import watcher


def test_created_pdf_is_ingested(tmp_path: Path, monkeypatch) -> None:
    session = Mock()
    session_context = Mock()
    session_context.__enter__ = Mock(return_value=session)
    session_context.__exit__ = Mock(return_value=False)
    ingest = Mock()
    monkeypatch.setattr(watcher, "SessionLocal", Mock(return_value=session_context))
    monkeypatch.setattr(watcher, "ingest_pdf", ingest)
    handler = watcher.ResumeInboxHandler(Settings(resume_inbox_dir=tmp_path))
    pdf = tmp_path / "candidate.pdf"

    handler.on_created(FileCreatedEvent(str(pdf)))

    ingest.assert_called_once_with(session, pdf, handler.settings, copy_file=True)


def test_completed_browser_download_is_ingested_after_rename(tmp_path: Path, monkeypatch) -> None:
    session = Mock()
    session_context = Mock()
    session_context.__enter__ = Mock(return_value=session)
    session_context.__exit__ = Mock(return_value=False)
    ingest = Mock()
    monkeypatch.setattr(watcher, "SessionLocal", Mock(return_value=session_context))
    monkeypatch.setattr(watcher, "ingest_pdf", ingest)
    handler = watcher.ResumeInboxHandler(Settings(resume_inbox_dir=tmp_path))
    temporary = tmp_path / "candidate.pdf.crdownload"
    completed = tmp_path / "candidate.pdf"

    handler.on_created(FileCreatedEvent(str(temporary)))
    handler.on_moved(FileMovedEvent(str(temporary), str(completed)))

    ingest.assert_called_once_with(session, completed, handler.settings, copy_file=True)
