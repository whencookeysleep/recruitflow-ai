from pathlib import Path

from sqlalchemy.orm import Session
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from app.config import Settings
from app.database import SessionLocal
from app.services.resumes import ingest_pdf


class ResumeInboxHandler(FileSystemEventHandler):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".pdf":
            return
        with SessionLocal() as db:
            ingest_pdf(db, path, self.settings, copy_file=True)


def start_resume_watcher(settings: Settings) -> Observer:
    settings.resume_inbox_dir.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(ResumeInboxHandler(settings), str(settings.resume_inbox_dir), recursive=False)
    observer.daemon = True
    observer.start()
    return observer
