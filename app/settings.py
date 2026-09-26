from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and an optional .env file."""

    slot_extractor: str = "rule_based"
    openai_api_key: str | None = None
    openai_model: str | None = None
    flow_config_path: str = "config/flow.yaml"
    pricing_config_path: str = "config/pricing.yaml"
    asset_config_path: str = "config/assets.yaml"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
