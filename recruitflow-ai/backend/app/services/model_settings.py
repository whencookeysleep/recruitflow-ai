from sqlalchemy.orm import Session

from app.config import Settings
from app.models import SystemSetting
from app.schemas import AiModelSettingsOut, AiModelSettingsUpdate


AI_MODEL_KEY = "ai_model"


def configured_model(db: Session, settings: Settings) -> str:
    stored = db.get(SystemSetting, AI_MODEL_KEY)
    return stored.value if stored and stored.value else settings.openai_model


def effective_ai_settings(db: Session, settings: Settings) -> Settings:
    return settings.model_copy(update={"openai_model": configured_model(db, settings)})


def get_ai_model_settings(db: Session, settings: Settings) -> AiModelSettingsOut:
    return AiModelSettingsOut(
        model=configured_model(db, settings),
        provider=settings.ai_provider,
        base_url=settings.openai_base_url,
        api_key_configured=bool(settings.openai_api_key),
    )


def update_ai_model_settings(
    db: Session,
    payload: AiModelSettingsUpdate,
    settings: Settings,
) -> AiModelSettingsOut:
    db.merge(SystemSetting(key=AI_MODEL_KEY, value=payload.model))
    db.commit()
    return get_ai_model_settings(db, settings)
