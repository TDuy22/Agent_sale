from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime settings from environment variables and backend/.env.

    Relative paths are resolved against the backend directory, so the server works
    regardless of the current working directory.
    """

    slot_extractor: Literal["auto", "gemini", "openai", "rule_based"] = "auto"
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    flow_config_path: Path = Path("config/flow.yaml")
    pricing_config_path: Path = Path("config/pricing.yaml")
    asset_config_path: Path = Path("assets/assets.yaml")
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    @field_validator("flow_config_path", "pricing_config_path", "asset_config_path")
    @classmethod
    def _resolve_from_backend_dir(cls, path: Path) -> Path:
        return path if path.is_absolute() else BACKEND_DIR / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
