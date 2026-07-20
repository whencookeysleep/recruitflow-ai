from app.config import Settings
from app.schemas import AiModelSettingsUpdate
from app.services.model_settings import effective_ai_settings, update_ai_model_settings


def test_ai_model_setting_is_persisted_and_applied(db) -> None:
    settings = Settings(openai_model="default/model", _env_file=None)

    saved = update_ai_model_settings(
        db,
        AiModelSettingsUpdate(model="deepseek/deepseek-v4-flash"),
        settings,
    )
    effective = effective_ai_settings(db, settings)

    assert saved.model == "deepseek/deepseek-v4-flash"
    assert effective.openai_model == "deepseek/deepseek-v4-flash"
