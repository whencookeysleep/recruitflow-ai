from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import get_settings
from app.database import create_all
from app.services.watcher import start_resume_watcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.resume_inbox_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    create_all()
    observer = start_resume_watcher(settings)
    try:
        yield
    finally:
        observer.stop()
        observer.join(timeout=5)


app = FastAPI(title="RecruitFlow AI API", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
